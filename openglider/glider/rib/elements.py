import logging
import math
from typing import List, TYPE_CHECKING

import euklid
import numpy as np
import openglider
from openglider.glider.shape import Shape
from openglider.lines import Node
from openglider.utils.dataclass import dataclass
from openglider.vector.polygon import Circle, Ellipse

if TYPE_CHECKING:
    from openglider.glider.rib.rib import Rib
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)

@dataclass
class RigidFoil:
    start: float = -0.1
    end: float = 0.1
    distance: float = 0.005
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

    def get_3d(self, rib: "Rib"):
        return [rib.align(p, scale=False) for p in self.get_flattened(rib)]

    def get_length(self, rib: "Rib"):
        return self.get_flattened(rib).get_length()

    def get_flattened(self, rib: "Rib"):
        return self._get_flattened(rib).fix_errors()

    def _get_flattened(self, rib: "Rib"):
        max_segment = 0.005  # 5mm
        profile = rib.profile_2d
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


@dataclass
class GibusArcs:
    """
    A Reinforcement, in the shape of an arc, to reinforce attachment points
    """

    position: float
    size: float = 0.05
    material_code: str = ""

    size_abs: bool = True

    def get_3d(self, rib: "Rib", num_points: int=10) -> euklid.vector.PolyLine3D:
        # create circle with center on the point
        gib_arc = self.get_flattened(rib, num_points=num_points)

        return rib.align_all(gib_arc, scale=False)
        #return [rib.align([p[0], p[1], 0], scale=False) for p in gib_arc]

    def get_flattened(self, rib: "Rib", num_points: int=10) -> euklid.vector.PolyLine2D:
        # get center point
        profile = rib.profile_2d
        start = profile(self.position)
        point_1 = profile.curve.get(start)

        if self.size_abs:
            # reverse scale now
            size = self.size / rib.chord
        else:
            size = self.size
        
        n = profile.normvectors.get(start)

        point_2 = point_1 + n * size  # get outside start point
        circle = Circle.from_center_p2(point_1, point_2).get_sequence()

        cuts = circle.cut(profile.curve)

        cut1 = cuts[0]
        cut2 = cuts[-1]

        return circle.get(cut1[0], cut2[0]) + profile.curve.get(cut2[1], cut1[1])


class CellAttachmentPoint(Node):
    ballooned=False

    def __init__(self, cell, name, cell_pos, rib_pos, force=None, offset=None):
        super().__init__(node_type=self.NODE_TYPE.UPPER)
        self.cell = cell
        self.cell_pos = cell_pos
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

        if offset is None:
            offset = 0
        self.offset: float = offset

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {
            "cell": self.cell,
            "cell_pos": self.cell_pos,
            "rib_pos": self.rib_pos,
            "name": self.name,
            "force": self.force
        }

    def get_position(self) -> euklid.vector.Vector3D:
        ik = self.cell.rib1.profile_2d(self.rib_pos)

        if self.rib_pos in (-1, 1):
            p1 = self.cell.rib1.profile_3d.get(ik)
            p2 = self.cell.rib2.profile_3d.get(ik)
            self.vec = p1 + (p2 - p1)*self.cell_pos
        else:
            self.vec = self.cell.midrib(self.cell_pos, ballooning=self.ballooned)[ik]
            
        return self.vec
    
    def get_position_2d(self, shape: Shape, glider: "Glider") -> euklid.vector.Vector2D:
        cell_no = glider.cells.index(self.cell) + shape.has_center_cell

        return shape.get_point(cell_no+self.cell_pos, self.rib_pos)


# Node from lines
class AttachmentPoint(Node):

    def __init__(self, rib, name, rib_pos, force=None, offset=None):
        super().__init__(node_type=self.NODE_TYPE.UPPER)
        self.rib = rib
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

        if offset is None:
            offset = -0.01
        self.offset: float = offset

        self.protoloops = 0
        self.protoloop_distance = 0.02

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {"rib": self.rib,
                "name": self.name,
                "rib_pos": self.rib_pos,
                "force": self.force
                }

    def get_position(self) -> euklid.vector.Vector3D:
        # todo: PROFILE3D -> return euklid vector
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec
    
    def get_position_2d(self, shape: Shape, glider: "Glider") -> euklid.vector.Vector2D:
        rib_no = glider.ribs.index(self.rib)

        return shape.get_point(rib_no, self.rib_pos)

