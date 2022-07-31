import typing
import numpy as np
from numpy.linalg import norm
import euklid
import pyfoil

from openglider.airfoil.profile_3d import Profile3D

from openglider.glider.rib.rib import Rib
from openglider.utils import linspace
from openglider.utils.cache import cached_property

if typing.TYPE_CHECKING:
    from openglider.glider.glider import Glider

class SingleSkinRib(Rib):
    def __init__(self, profile_2d=None, startpoint=None,
                 chord=1., arcang=0, aoa_absolute=0, zrot=0, xrot=0., glide=1,
                 name="unnamed rib", startpos=0.,
                 rigidfoils=None, holes=None, material=None,
                 single_skin_par=None, sharknose=None):
        super(SingleSkinRib, self).__init__(profile_2d=profile_2d, 
                                            startpoint=startpoint,
                                            chord=chord,
                                            arcang=arcang,
                                            aoa_absolute=aoa_absolute,
                                            zrot=zrot,
                                            xrot=xrot,
                                            glide=glide,
                                            name=name,
                                            startpos=startpos,
                                            rigidfoils=rigidfoils,
                                            holes=holes,
                                            material=material,
                                            sharknose=sharknose)
        self.single_skin_par = {
            "att_dist": 0.02,
            "height": 0.8,
            "continued_min": True,
            "continued_min_angle": -0.03,
            "continued_min_delta_y": 0,
            "continued_min_end": 0.94,
            "continued_min_x": 0,
            "double_first": True,
            "le_gap": True,
            "straight_te": True,
            "te_gap": False,
            "num_points": 30
        }

        self._hull = None

        if single_skin_par:
            self.single_skin_par.update(single_skin_par)
            self.single_skin_par["num_points"] = 30
            #print(self.single_skin_par)

        # we have to apply this function once for the profile2d
        # this will change the position of the attachmentpoints!
        # therefore it shouldn't be placed int the get_hull function
        if self.single_skin_par['continued_min']: 
            self.apply_continued_min()

    def apply_continued_min(self):
        self.profile_2d = self.profile_2d.move_nearest_point(self.single_skin_par['continued_min_end'])
        data = np.array(self.profile_2d.curve.tolist())
        x, y = data.T
        min_index = y.argmin()
        y_min = y[min_index]
        new_y = []
        for i, xy in enumerate(data):
            if i > min_index and (self.single_skin_par['continued_min_end'] - xy[0]) > -1e-8:
                new_y += [y_min + (xy[0] - data[min_index][0]) * np.tan(self.single_skin_par['continued_min_angle'])]
            else:
                new_y += [xy[1]]

        data = np.array([x, new_y]).T.tolist()
        self.profile_2d = pyfoil.Airfoil(data)

    @classmethod
    def from_rib(cls, rib, single_skin_par):
        json_dict = rib.__json__()
        if "xrot" in single_skin_par:
            json_dict["xrot"] = single_skin_par.pop("xrot")
        json_dict["single_skin_par"] = single_skin_par
        single_skin_rib = cls(**json_dict)
        return single_skin_rib

    def __json__(self):
        json_dict = super().__json__()
        json_dict["single_skin_par"] = self.single_skin_par
        return json_dict

    def get_hull(self, glider: "Glider"=None) -> pyfoil.Airfoil:
        '''
        returns a modified profile2d
        '''
        if glider is None:
            return self._hull

        profile = self.profile_2d
        attach_pts = self.get_attachment_points(glider)
        fixed_positions = list(set([att.rib_pos for att in attach_pts] + [1]))

        if len(fixed_positions) > 1:
            span_list = []
            fixed_positions.sort()

            # computing the bow start and end points
            for i in range(len(fixed_positions)-1):

                # the profile  has a normed chord of 1
                # so we have to normalize the "att_dist" which is the thickness of
                # rib between two bows. normally something like 2cm
                # length of the flat part at the attachment point
                le_gap = self.single_skin_par["att_dist"] / self.chord / 2
                te_gap = le_gap

                # le_gap is the gap between the FIRST BOW start and the attachment point next
                # to this point. (before)
                if i == 0 and not self.single_skin_par["le_gap"]: 
                    le_gap = 0

                # te_gap is the gap between the LAST BOW end and the trailing edge
                if i == len(fixed_positions)-2 and not self.single_skin_par["te_gap"]:
                    te_gap = 0

                span_list.append([fixed_positions[i] + le_gap, fixed_positions[i+1] - te_gap])

            for k, span in enumerate(span_list):
                if self.single_skin_par["double_first"] and k == 0:
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
                for x in linspace(span[0], span[1], self.single_skin_par["num_points"])[:-1]:
                    profile = profile.insert_point(x)

            # construct shifting function:
            for i, span in enumerate(span_list):
                # parabola from 3 points
                if self.single_skin_par["double_first"] and i == 0:
                    continue
                x0 = np.array(profile.profilepoint(span[0]))
                x1 = np.array(profile.profilepoint(span[1]))
                x_mid = (x0 + x1)[0] / 2
                height = abs(profile.profilepoint(-x_mid)[1] - 
                             profile.profilepoint(x_mid)[1])
                height *= self.single_skin_par["height"] # anything bewtween 0..1
                y_mid = profile.profilepoint(x_mid)[1] + height
                x_max = np.array([norm(x1 - x0) / 2, height])

                def foo(x, upper):
                    if not upper and x[0] > x0[0] and x[0] < x1[0]:
                        if self.single_skin_par["straight_te"] and i == len(span_list) - 1:
                            return self.straight_line(x, x0, x1)
                        else:
                            return self.parabola(x, x0, x1, x_max)
                    else:
                        return x


                new_data = [
                    foo(p, upper=index < profile.noseindex) for index, p in enumerate(profile.curve)
                ]

                profile = pyfoil.Airfoil(new_data)

        self._hull = profile
        return profile

    @staticmethod
    def straight_line(x, x0, x1):
        x_proj = (x - x0).dot(x1 - x0) / norm(x1 - x0)**2
        return euklid.vector.Vector2D(list(x0 + (x1 - x0) * x_proj))

    @staticmethod
    def parabola(x, x0, x1, x_max):
        """parabola used for singleskin ribs
        x, x0, x1, x_max ... numpy 2d arrays
        xmax = np.sqrt((x1 - x0)**2 + (y1 - y0)**2)"""
        x_proj = (x - x0).dot(x1 - x0) / norm(x1 - x0)**2
        x_proj = (x_proj - 0.5) * 2
        y_proj = -x_proj **2
        x = np.array([x_proj, y_proj]) * x_max
        c = (x1 - x0)[0] / norm(x1 - x0)
        s = (x1 - x0)[1] / norm(x1 - x0)
        rot = np.array([[c, -s], [s, c]])
        null = - x_max
        return euklid.vector.Vector2D(list(rot.dot(x - null) + x0))
