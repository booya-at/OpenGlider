from __future__ import annotations

import math
import typing
import numpy as np
import euklid
import pyfoil

from openglider.glider.rib.rib import Rib
from openglider.utils import linspace
from openglider.utils.dataclass import Field, BaseModel
from openglider.utils.cache import cached_function

from openglider.vector.unit import Angle, Length, Percentage

if typing.TYPE_CHECKING:
    pass


class SingleSkinParameters(BaseModel):
    att_dist: Length | Percentage = Length("2cm")
    height: Percentage = Percentage(0.8)
    continued_min: bool = True
    continued_min_angle: Angle = Angle(-0.03)
    continued_min_delta_y : float = 0.
    continued_min_end: Percentage = Percentage("94%")
    continued_min_x: Percentage = Percentage(0)
    double_first: bool = True
    le_gap: bool = True
    straight_te: bool = True
    te_gap: bool = False
    num_points: int = 30




class SingleSkinRib(Rib):
    single_skin_par: SingleSkinParameters = Field(default_factory=SingleSkinParameters)

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.single_skin_par.continued_min:
            self.apply_continued_min()

    def apply_continued_min(self) -> None:
        self.profile_2d = self.profile_2d.move_nearest_point(self.single_skin_par.continued_min_end)
        data = np.array(self.profile_2d.curve.tolist())
        x, y = data.T
        min_index = y.argmin()
        y_min = y[min_index]
        new_y = []
        for i, xy in enumerate(data):
            if i > min_index and (self.single_skin_par.continued_min_end - xy[0]) > -1e-8:
                new_y += [y_min + (xy[0] - data[min_index][0]) * np.tan(self.single_skin_par.continued_min_angle.si)]
            else:
                new_y += [xy[1]]

        data = np.array([x, new_y]).T.tolist()
        self.profile_2d = pyfoil.Airfoil(data)

    @classmethod
    def from_rib(cls, rib: Rib, single_skin_par: SingleSkinParameters, xrot: Angle | None) -> SingleSkinRib:
        json_dict = rib.__json__()  # type: ignore
        if xrot is not None: 
            json_dict['xrot'] = xrot

        return cls(**json_dict, single_skin_par=single_skin_par)

    def __json__(self) -> dict[str, typing.Any]:
        json_dict = super().__json__()  # type: ignore
        json_dict["single_skin_par"] = self.single_skin_par
        return json_dict

    @cached_function("self", exclude=["attachment_points"], generator=lambda rib: [p.rib_pos for p in rib.attachment_points])
    def get_hull(self) -> pyfoil.Airfoil:
        profile = self.profile_2d
        attach_pts = self.attachment_points
        fixed_positions = list(set([att.rib_pos.si for att in attach_pts] + [1.]))

        if len(fixed_positions) > 1:
            span_list = []
            fixed_positions.sort()

            # computing the bow start and end points
            for i in range(len(fixed_positions)-1):

                # the profile  has a normed chord of 1
                # so we have to normalize the "att_dist" which is the thickness of
                # rib between two bows. normally something like 2cm
                # length of the flat part at the attachment point
                le_gap = self.convert_to_percentage(self.single_skin_par.att_dist) / 2
                te_gap = le_gap

                # le_gap is the gap between the FIRST BOW start and the attachment point next
                # to this point. (before)
                if i == 0 and not self.single_skin_par.le_gap: 
                    le_gap = Percentage(0.)

                # te_gap is the gap between the LAST BOW end and the trailing edge
                if i == len(fixed_positions)-2 and not self.single_skin_par.te_gap:
                    te_gap = Percentage(0.)

                span_list.append([fixed_positions[i] + le_gap.si, fixed_positions[i+1] - te_gap.si])

            for k, span in enumerate(span_list):
                if self.single_skin_par.double_first and k == 0:
                    continue # do not insert points between att for double-first ribs (a-b)

                # first we insert the start and end point of the bow
                profile = profile.insert_point(span[0])
                profile = profile.insert_point(span[1])

                # now we remove all points between these two points
                # we have to use a tolerance to not delete the start and end points of the bow.
                # problem: the x-value of a point inserted in a profile can have a slightly different
                # x-value
                profile = profile.remove_points(span[0], span[1], tolerance=1e-5)

                # insert sequence of xvalues between start and end. endpoint=False is necessary because 
                # start and end are already inserted.
                for x in linspace(span[0], span[1], self.single_skin_par.num_points)[:-1]:
                    profile = profile.insert_point(x)

            # construct shifting function:
            for i, span in enumerate(span_list):
                # parabola from 3 points
                if self.single_skin_par.double_first and i == 0:
                    continue

                x_start = profile.profilepoint(span[0])
                x_end = profile.profilepoint(span[1])

                x_mid = (x_start + x_end)[0] / 2

                height = (profile.profilepoint(-x_mid) - profile.profilepoint(x_mid)).length()
                height *= self.single_skin_par.height.si # anything bewtween 0..1
                
                y_vec = euklid.vector.Rotation2D(math.pi/2).apply(x_end - x_start).normalized() * height

                def convert_point(x: euklid.vector.Vector2D, upper: bool) -> euklid.vector.Vector2D:
                    if upper or x[0] < x_start[0] or x[0] > x_end[0]:
                        return x
                    else:
                        if self.single_skin_par.straight_te and i == len(span_list) - 1:
                            # last span part (->trailing edge)
                            return self.straight_line(x, x_start, x_end)
                        else:
                            return self.parabola(x, x_start, x_end, y_vec)

                new_data = [
                    convert_point(p, upper=index < profile.noseindex) for index, p in enumerate(profile.curve)
                ]

                profile = pyfoil.Airfoil(new_data)

        return profile

    @staticmethod
    def straight_line(x: euklid.vector.Vector2D, x0: euklid.vector.Vector2D, x1: euklid.vector.Vector2D) -> euklid.vector.Vector2D:
        x_proj = (x - x0).dot(x1 - x0) / (x1 - x0).length()**2
        return x0 + (x1 - x0) * x_proj

    @staticmethod
    def parabola(x: euklid.vector.Vector2D, p_start: euklid.vector.Vector2D, p_end: euklid.vector.Vector2D, y_vector: euklid.vector.Vector2D) -> euklid.vector.Vector2D:
        diff = p_end - p_start
        x_proj = (x - p_start).dot(diff) / diff.dot(diff)  # [0,1]

        x_proj_2 = (x_proj - 0.5) * 2  # [-1 -> 0 -> 1]
        y_proj = (-x_proj_2) **2  # [1 -> 0 -> 1]

        return p_start + diff * x_proj + y_vector * (1-y_proj)
