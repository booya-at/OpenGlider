from __future__ import annotations

from abc import ABC
import logging
import math
from typing import TYPE_CHECKING

import euklid
import numpy as np
from openglider.utils.dataclass import BaseModel, dataclass
from openglider.vector.unit import Length, Percentage

if TYPE_CHECKING:
    from openglider.glider.rib.rib import Rib
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)


class RigidFoilBase(ABC, BaseModel):
    name: str = "unnamed"
    start: Percentage = Percentage(-0.1)
    end: Percentage = Percentage(0.1)
    distance: Length | Percentage = Length("3mm")

    cap_length: Length = Length("2cm")
    tension: Percentage = Percentage("98%")

    def get_3d(self, rib: Rib) -> euklid.vector.PolyLine3D:
        return euklid.vector.PolyLine3D([rib.align(p, scale=False) for p in self.get_flattened(rib)])

    def get_length(self, rib: Rib) -> float:
        return self.get_flattened(rib).get_length() * self.tension.si

    def get_flattened(self, rib: Rib, glider: Glider=None) -> euklid.vector.PolyLine2D:
        return self._get_flattened(rib, glider).fix_errors()
    
    def _get_flattened(self, rib: Rib, glider: Glider=None) -> euklid.vector.PolyLine2D:
        raise NotImplementedError()

    def get_cap_radius(self, start: bool) -> tuple[Length, Percentage]:
        raise NotImplementedError



class RigidFoil(RigidFoilBase):
    circle_radius: Length = Length("3cm")

    def func(self, pos: float, radius: Percentage) -> float:
        dsq = None
        if -0.05 <= pos - self.start.si < radius.si:
            dsq = radius.si**2 - (radius.si + self.start.si - pos)**2
        if -0.05 <= self.end.si - pos < radius.si:
            dsq = radius.si**2 - (radius.si + pos - self.end.si)**2

        if dsq is not None:
            dsq = max(dsq, 0)
            return (radius.si - np.sqrt(dsq)) * 0.35
        return 0.

    def get_cap_radius(self, start: bool) -> tuple[Length, Percentage]:
        return -self.circle_radius, Percentage(0.35)

    def _get_flattened(self, rib: Rib, glider: Glider=None) -> euklid.vector.PolyLine2D:
        max_segment = 0.005  # 5mm
        profile = rib.get_hull()
        profile_normvectors = profile.normvectors

        start = profile.get_ik(self.start)
        end = profile.get_ik(self.end)

        point_range = []
        last_node = None
        for p in profile.curve.get(start, end).nodes:
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

        # convert to unitless percentage (everything is scaled later)
        distance = rib.convert_to_percentage(self.distance)
        radius = rib.convert_to_percentage(self.circle_radius)

        nodes = [
            (profile.curve.get(ik) - profile_normvectors.get(ik) * (distance.si + self.func(x, radius))) * rib.chord
            for ik, x in zip(indices, point_range)
            ]

        return euklid.vector.PolyLine2D(nodes)


class _RigidFoilCurved(RigidFoilBase):
    append_curve: bool = True
    straight_part: Length = Length(0)

    def _get_flattened(self, rib: Rib, glider: Glider=None) -> euklid.vector.PolyLine2D:
        profile = rib.get_hull()

        start = profile.get_ik(self.start.si)
        end = profile.get_ik(self.end.si)

        distance = rib.convert_to_chordlength(self.distance)

        rigidfoil_curve = (profile.curve.get(start, end) * rib.chord).offset(-distance.si).fix_errors()
        inner_curve = rigidfoil_curve

        segments = rigidfoil_curve.get_segments()
        rot_90 = euklid.vector.Rotation2D(math.pi/2)

        # first ending
        _radius, _amount = self.get_cap_radius(True)
        radius = _radius.si
        amount = _amount.si

        if radius > 0:
            cp1 = rigidfoil_curve.get(0)
            cp2 = cp1 - segments[0].normalized() * radius * amount
            cp3 = cp1 - segments[0].normalized() * radius + rot_90.apply(segments[0].normalized()) * radius * amount
        else:
            cp2_ik = rigidfoil_curve.walk(0, abs(radius * amount))
            cp2 = rigidfoil_curve.get(cp2_ik)
            cp1_ik = rigidfoil_curve.walk(0, abs(radius))
            cp1 = rigidfoil_curve.get(cp1_ik)
            cp3 = rigidfoil_curve.get(0) - rot_90.apply(segments[0].normalized()) * radius * amount
            inner_curve = inner_curve.get(cp1_ik, len(inner_curve)-1)


        ending_1 = euklid.spline.BSplineCurve([cp3, cp2, cp1]).get_sequence(10).get(0, 9).nodes
        if self.straight_part:
            ending_1.insert(0, ending_1[0] + (ending_1[0] - ending_1[1]).normalized() * self.straight_part.si)

        # second ending
        _radius, _amount = self.get_cap_radius(False)
        radius = _radius.si
        amount = _amount.si
        end_ik = len(rigidfoil_curve)-1
        if radius > 0:
            cp1 = rigidfoil_curve.get(end_ik)
            cp2 = cp1 + segments[-1].normalized() * radius * amount
            cp3 = cp1 + segments[-1].normalized() * radius + rot_90.apply(segments[-1].normalized()) * radius * amount
        else:
            cp2_ik = rigidfoil_curve.walk(end_ik, -abs(radius * amount))
            cp2 = rigidfoil_curve.get(cp2_ik)
            cp1_ik = rigidfoil_curve.walk(end_ik, -abs(radius))
            cp1 = rigidfoil_curve.get(cp1_ik)
            cp3 = rigidfoil_curve.get(end_ik) - rot_90.apply(segments[-1].normalized()) * radius * amount
            inner_curve = inner_curve.get(0, cp1_ik)


        ending_2 = euklid.spline.BSplineCurve([cp1, cp2, cp3]).get_sequence(10).get(0, 9).nodes
        if self.straight_part:
            ending_2.append(ending_2[-1] + (ending_2[-1] - ending_2[-2]).normalized() * self.straight_part.si)

        return euklid.vector.PolyLine2D(ending_1 + inner_curve.nodes + ending_2)


class RigidFoilCurved(_RigidFoilCurved):
    circle_radius_start: Length = 0.03
    circle_amount_start: Percentage = 0.7

    circle_radius_end: Length = 0.03
    circle_amount_end: Percentage = 0.7

    def get_cap_radius(self, start: bool) -> tuple[Length, Percentage]:
        if start:
            return self.circle_radius_start, self.circle_amount_start
        else:
            return self.circle_radius_end, self.circle_amount_end


class RigidFoil2(_RigidFoilCurved):
    circle_radius: Length=Length("5cm")
    circle_amount: Percentage=Percentage(0.5)
    straight_part: Length = Length("2cm")

    def get_cap_radius(self, start: bool) -> tuple[Length, Percentage]:
        return self.circle_radius, self.circle_amount


@dataclass
class FoilCurve:
    front: float = 0
    end: float = 0.17

    def get_flattened(self, rib: Rib, numpoints: int=30) -> euklid.vector.PolyLine2D:
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
