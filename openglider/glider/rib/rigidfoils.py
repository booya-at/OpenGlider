import logging
import math
from typing import List, TYPE_CHECKING

import euklid
import numpy as np
from openglider.utils.dataclass import dataclass

if TYPE_CHECKING:
    from openglider.glider.rib.rib import Rib

logger = logging.getLogger(__name__)


@dataclass
class RigidFoilBase:
    start: float = -0.1
    end: float = 0.1
    distance: float = 0.005

    def get_3d(self, rib: "Rib"):
        return [rib.align(p, scale=False) for p in self.get_flattened(rib)]

    def get_length(self, rib: "Rib"):
        return self.get_flattened(rib).get_length()

    def get_flattened(self, rib: "Rib"):
        return self._get_flattened(rib).fix_errors()
    
    def _get_flattened(self, rib: "Rib"):
        raise NotImplementedError()


@dataclass
class RigidFoil(RigidFoilBase):
    circle_radius: float = 0.03

    def func(self, pos: float):
        dsq = None
        if -0.05 <= pos - self.start < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + self.start - pos)**2
        if -0.05 <= self.end - pos < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + pos - self.end)**2

        if dsq is not None:
            dsq = max(dsq, 0)
            return (self.circle_radius - np.sqrt(dsq)) * 0.35
        return 0

    def get_cap_radius(self, start: bool):
        return self.circle_radius, 1

    def _get_flattened(self, rib: "Rib"):
        max_segment = 0.005  # 5mm
        profile = rib.get_hull()
        profile_normvectors = profile.normvectors

        start = profile.get_ik(self.start)
        end = profile.get_ik(self.end)

        point_range = []
        last_node = None
        for p in profile.curve.get(start, end):
            sign = -1 if p[1] > 0 else +1

            if last_node is not None:
                diff = (p - last_node).length() * rib.chord
                if diff > max_segment:
                    segments = int(math.ceil(diff/max_segment))
                    point_range += list(np.linspace(point_range[-1], sign*p[0], segments))[1:]
                else:
                    point_range.append(sign*p[0])
            else:
                point_range.append(sign*p[0])

            last_node = p

        indices = [profile(x) for x in point_range]

        nodes = [
            (profile.curve.get(ik) - profile_normvectors.get(ik) * (self.distance/rib.chord + self.func(x))) * rib.chord 
            for ik, x in zip(indices, point_range)
            ]

        return euklid.vector.PolyLine2D(nodes)


class _RigidFoilCurved(RigidFoilBase):
    def get_cap_radius(self, start: bool):
        raise NotImplementedError

    def _get_flattened(self, rib: "Rib"):
        profile = rib.get_hull()

        start = profile.get_ik(self.start)
        end = profile.get_ik(self.end)

        rigidfoil_curve = (profile.curve.get(start, end) * rib.chord).offset(-self.distance).fix_errors()
        segments = rigidfoil_curve.get_segments()
        rot_90 = euklid.vector.Rotation2D(math.pi/2)

        # first ending
        radius, amount = self.get_cap_radius(True)
        cp1 = rigidfoil_curve.get(0)
        cp2 = cp1 - segments[0].normalized() * radius * amount
        cp3 = cp1 - segments[0].normalized() * radius + rot_90.apply(segments[0].normalized()) * radius * amount

        ending_1 = euklid.spline.BSplineCurve([cp3, cp2, cp1]).get_sequence(10).get(0, 9)

        # second ending
        radius, amount = self.get_cap_radius(False)
        cp1 = rigidfoil_curve.get(len(rigidfoil_curve)-1)
        cp2 = cp1 + segments[-1].normalized() * radius * amount
        cp3 = cp1 + segments[-1].normalized() * radius + rot_90.apply(segments[-1].normalized()) * radius * amount

        ending_2 = euklid.spline.BSplineCurve([cp1, cp2, cp3]).get_sequence(10).get(0, 9)

        return euklid.vector.PolyLine2D(ending_1.nodes + rigidfoil_curve.nodes + ending_2.nodes)

@dataclass
class RigidFoilCurved(_RigidFoilCurved):
    circle_radius_start: float = 0.03
    circle_amount_start: float = 0.7

    circle_radius_end: float = 0.03
    circle_amount_end: float = 0.7

    def get_cap_radius(self, start: bool):
        if start:
            return self.circle_radius_start, self.circle_amount_start
        else:
            return self.circle_radius_end, self.circle_amount_end


@dataclass
class RigidFoil2(_RigidFoilCurved):
    circle_radius: float=0.05
    circle_amount: float=0.5

    def get_cap_radius(self, start: bool):
        return self.circle_radius, self.circle_amount


@dataclass
class FoilCurve(object):
    front: float = 0
    end: float = 0.17

    def get_flattened(self, rib: "Rib", numpoints: int=30):
        curve = [
            [self.end, 0.75],
            [self.end-0.05, 1],
            [self.front, 0],
            [self.end-0.05, -1],
            [self.end, -0.75]
        ]
        profile = rib.profile_2d

        controlpoints = [profile.align(point)*rib.chord for point in curve]

        return euklid.spline.BezierCurve(controlpoints).get_sequence(numpoints)
