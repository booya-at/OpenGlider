from __future__ import annotations
import math

from typing import Any, Dict, List, Literal
import numpy as np
import euklid

from openglider.airfoil import Profile2D
from openglider.utils.distribution import Distribution
from openglider.utils.types import CurveType
# TODO: FIX!

class BezierProfile2D(Profile2D):
    # TODO make new fit bezier method to set the second x value of the
    # controllpoints to zero.
    def __init__(self, data: euklid.vector.PolyLine2D=None, name: str="unnamed",
                 upper_spline: CurveType=None, lower_spline: CurveType=None):
        super().__init__(data=data, name=name)
        self.curve = self.normalized().curve
        if upper_spline is None:
            upper_spline = self.fit_upper()
            
        self.upper_spline = upper_spline

        if lower_spline is None:
            lower_spline = self.fit_lower()
        
        self.lower_spline = lower_spline

        self.apply_splines()

    def __json__(self) -> dict[str, Any]:
        dct = super().__json__()
        dct.update({'upper_spline': self.upper_spline,
                    'lower_spline': self.lower_spline})
        return dct

    def fit_upper(self, num: int=100, dist: Literal["const"] | Literal["sin"] | None=None, control_num: int=8) -> CurveType:
        upper = self.curve.nodes[:self.noseindex + 1]
        upper_smooth = self.make_smooth_dist(upper, num, dist)
        
        if self.upper_spline is not None:
            return self.upper_spline.fit(upper_smooth, control_num)  # type: ignore
        else:
            return euklid.spline.BSplineCurve.fit(upper_smooth, control_num)

    def fit_lower(self, num: int=100, dist: Literal["const"] | Literal["sin"] | None=None, control_num: int=8) -> CurveType:
        lower = self.curve.nodes[self.noseindex:]
        lower_smooth = self.make_smooth_dist(lower, num, dist, upper=False)
        
        if self.lower_spline:
            return self.lower_spline.fit(lower_smooth, control_num)  # type: ignore
        else:
            return euklid.spline.BSplineCurve.fit(lower_smooth, control_num)  # type: ignore

    def fit_region(self, start: float, stop: float, num_points: int, control_points: list[euklid.vector.Vector2D]) -> CurveType:
        smoothened = euklid.vector.PolyLine2D([self.get(x) for x in np.linspace(start, stop, num=num_points)])
        return euklid.spline.BezierCurve.fit(smoothened, numpoints=num_points)  # type: ignore

    def fit_profile(self, num_points: int, control_points: list[euklid.vector.Vector2D]) -> None:
        # todo: classmethod
        self.upper_spline = self.fit_region(-1., 0., num_points, control_points)
        self.lower_spline = self.fit_region(0., 1., num_points, control_points)

    def apply_splines(self, num: int=70) -> None:
        upper = self.upper_spline.get_sequence(num)
        lower = self.lower_spline.get_sequence(num)

        self.data = euklid.vector.PolyLine2D(upper.tolist() + lower.tolist()[1:])

    def make_smooth_dist(self, points: list[euklid.vector.Vector2D], num: int=70, dist: Literal["const"] | Literal["sin"] | None=None, upper: bool=True) -> euklid.vector.PolyLine2D:
        # make array [[length, x, y], ...]
        if not dist:
            return euklid.vector.PolyLine2D(points)
        length = [0.]
        for i, point in enumerate(points[1:]):
            length.append(length[-1] + (point - points[i]).length())
        interpolation_x = euklid.vector.Interpolation(list(zip(length, [p[0] for p in points])))
        interpolation_y = euklid.vector.Interpolation(points)

        def get_point(dist: float) -> euklid.vector.Vector2D:
            x = interpolation_x.get_value(dist)
            return euklid.vector.Vector2D([x, interpolation_y.get_value(x)])

        if dist == "const":
            distribution = Distribution.from_linear(num, 0, length[-1]).data
        elif dist == "sin":
            if upper:
                distribution = [math.sin(i) * length[-1] for i in np.linspace(0, np.pi / 2, num)]
            else:
                distribution = [abs(1 - math.sin(i)) * length[-1] for i in np.linspace(0, np.pi / 2, num)]
        else:
            return points

        return euklid.vector.PolyLine2D([get_point(d) for d in distribution])

    @classmethod
    def from_profile_2d(cls, profile_2d: Profile2D) -> BezierProfile2D:
        return cls(profile_2d.curve, profile_2d.name)
