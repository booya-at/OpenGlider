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

    def get_position(self, glider=None) -> euklid.vector.Vector3D:
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
    def __init__(self, rib, name, rib_pos, force=None, offset=None, protoloops=0, protoloop_distance=0.02, protoloop_distance_absolute=True):
        super().__init__(node_type=self.NODE_TYPE.UPPER)
        self.rib = rib
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

        if offset is None:
            offset = -0.01
        self.offset: float = offset

        self.protoloops = protoloops
        self.protoloop_distance = protoloop_distance
        self.protoloop_distance_absolute = protoloop_distance_absolute

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {"rib": self.rib,
                "name": self.name,
                "rib_pos": self.rib_pos,
                "force": self.force,
                "protoloops": self.protoloops,
                "protoloop_distance": self.protoloop_distance,
                "protoloop_distance_absolute": self.protoloop_distance_absolute
                }
    
    def get_x_values(self, rib: "Rib"):
        positions = [self.rib_pos]

        if self.protoloops:
            hull = rib.get_hull()
            ik_start = hull.get_ik(self.rib_pos)

            for i in range(self.protoloops):
                diff = (i+1) * self.protoloop_distance
                if self.protoloop_distance_absolute:
                    front_ik = hull.curve.walk(ik_start, -diff / rib.chord)
                    back_ik = hull.curve.walk(ik_start, diff / rib.chord)

                    positions.append(hull.curve.get(front_ik)[0])
                    positions.append(hull.curve.get(back_ik)[0])
                else:
                    positions.append(self.rib_pos-diff)
                    positions.append(self.rib_pos+diff)
        
        return positions

    def get_position(self, glider=None) -> euklid.vector.Vector3D:
        # todo: PROFILE3D -> return euklid vector
        self.vec = self.rib.get_profile_3d(glider)[self.rib.profile_2d(self.rib_pos)]
        return self.vec
    
    def get_position_2d(self, shape: Shape, glider: "Glider") -> euklid.vector.Vector2D:
        rib_no = glider.ribs.index(self.rib)

        return shape.get_point(rib_no, self.rib_pos)

