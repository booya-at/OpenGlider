from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Dict, Optional
import logging

import euklid
from openglider.glider.shape import Shape
from openglider.lines.node import NODE_TYPE_ENUM, Node
from openglider.utils.dataclass import BaseModel, dataclass
from openglider.vector.polygon import Circle
from openglider.vector.unit import Percentage, Length

if TYPE_CHECKING:
    from openglider.glider.rib.rib import Rib
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)


class RoundReinforcement(BaseModel):
    """
    A Reinforcement, in the shape of an arc, to reinforce attachment points
    """
    position: Percentage
    size: Length | Percentage = Length("4cm")
    material_code: str = ""

    def get_3d(self, rib: Rib, num_points: int=10) -> list[euklid.vector.PolyLine3D]:
        # create circle with center on the point
        polygons = self.get_flattened(rib, num_points=num_points)
        aligned_polygons = []
        for polygon in polygons:

            aligned_polygons.append(rib.align_all(polygon, scale=False))
        
        return aligned_polygons

    def get_flattened(self, rib: Rib, num_points: int=10) -> list[euklid.vector.PolyLine2D]:
        # get center point
        profile = rib.profile_2d
        start = profile(self.position)
        point_1 = profile.curve.get(start)

        size = rib.convert_to_chordlength(self.size).si
        
        n = profile.normvectors.get(start)

        point_2 = point_1 + n * size  # get outside start point
        circle = Circle.from_center_p2(point_1, point_2).get_sequence()

        return circle.bool_union(profile.curve)


# Node from lines
class AttachmentPoint(Node):
    rib_pos: Percentage

    node_type: NODE_TYPE_ENUM = Node.NODE_TYPE.UPPER
    offset: Length = Length("1cm")
    protoloops: int = 0
    protoloop_distance: Percentage | Length = Percentage("2%")

    def __repr__(self) -> str:
        return f"<Attachment point '{self.name}' ({self.rib_pos})>"

    def __json__(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "rib_pos": self.rib_pos,
            "force": self.force,
            "protoloops": self.protoloops,
            "protoloop_distance": self.protoloop_distance,
        }
    
    @classmethod
    def __from_json__(self, **data: Any) -> AttachmentPoint:
        data["force"] = euklid.vector.Vector3D(data["force"])
        return AttachmentPoint(**data)


    
    def get_x_values(self, rib: Rib) -> list[float]:
        positions = [self.rib_pos.value]

        if self.protoloops:
            hull = rib.get_hull()
            ik_start = hull.get_ik(self.rib_pos)

            for i in range(self.protoloops):
                diff = (i+1) * self.protoloop_distance
                if isinstance(self.protoloop_distance, Length):
                    front_ik = hull.curve.walk(ik_start, (-diff / rib.chord).si)
                    back_ik = hull.curve.walk(ik_start, (diff / rib.chord).si)

                    positions.append(hull.curve.get(front_ik)[0])
                    positions.append(hull.curve.get(back_ik)[0])
                else:
                    positions.append((self.rib_pos-diff).si)
                    positions.append((self.rib_pos+diff).si)
        
        return positions
    
    @classmethod
    def calculate_force_rib_aligned(self, rib: Rib, force: float | None=None) -> euklid.vector.Vector3D:
        if force is None:
            force = self.force.length()
        return rib.rotation_matrix.apply([0, force, 0])

    def get_position(self, rib: Rib) -> euklid.vector.Vector3D:
        hull = rib.get_hull()
        profile_3d = rib.get_profile_3d()

        self.position = profile_3d.get(hull(self.rib_pos.si))

        return self.position
    
    def get_position_2d(self, shape: Shape, glider: Glider) -> euklid.vector.Vector2D:

        rib_no = None
        for i, rib in enumerate(glider.ribs):
            if self in rib.attachment_points:
                rib_no = i
        
        if rib_no is None:
            raise ValueError(f"no rib found for node: {self}")

        return shape.get_point(rib_no, self.rib_pos.si)