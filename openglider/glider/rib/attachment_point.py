from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Dict, Optional
import logging

import euklid
from openglider.glider.shape import Shape
from openglider.lines.node import Node, NODE_TYPE
from openglider.utils.dataclass import dataclass
from openglider.vector.polygon import Circle

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


# Node from lines
class AttachmentPoint(Node):
    rib_pos: float

    node_type = Node.NODE_TYPE.UPPER
    offset: float = -0.01
    protoloops: int = False
    protoloop_distance: float = 0.02
    protoloop_distance_absolute: bool = True
    
    def __init__(
        self, name: str,
        rib_pos: float,
        force: euklid.vector.Vector3D,
        offset: float=-0.01,
        protoloops: int=0,
        protoloop_distance: float=0.02,
        protoloop_distance_absolute: bool=True,
        node_type: Node.NODE_TYPE=Node.NODE_TYPE.UPPER
        ):
        
        super().__init__(node_type=Node.NODE_TYPE.UPPER, rib_pos=rib_pos, name=name, force=force)

        self.rib_pos = rib_pos
        self.name = name
        self.force = euklid.vector.Vector3D(force)

        self.offset = offset

        self.protoloops = protoloops
        self.protoloop_distance = protoloop_distance
        self.protoloop_distance_absolute = protoloop_distance_absolute

    def __repr__(self) -> str:
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "rib_pos": self.rib_pos,
            "force": self.force,
            "protoloops": self.protoloops,
            "protoloop_distance": self.protoloop_distance,
            "protoloop_distance_absolute": self.protoloop_distance_absolute
        }
    
    @classmethod
    def __from_json__(self, **data: Any) -> AttachmentPoint:
        data["force"] = euklid.vector.Vector3D(data["force"])
        return AttachmentPoint(**data)


    
    def get_x_values(self, rib: Rib) -> List[float]:
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
    
    @classmethod
    def calculate_force_rib_aligned(self, rib: Rib, force: Optional[float]=None) -> euklid.vector.Vector3D:
        if force is None:
            force = self.force.length()
        return rib.rotation_matrix.apply([0, force, 0])

    def get_position(self, rib: Rib) -> euklid.vector.Vector3D:
        hull = rib.get_hull()
        profile_3d = rib.get_profile_3d()

        self.position = profile_3d.get(hull(self.rib_pos))

        return self.position
    
    def get_position_2d(self, shape: Shape, glider: Glider) -> euklid.vector.Vector2D:

        rib_no = None
        for i, rib in enumerate(glider.ribs):
            if self in rib.attachment_points:
                rib_no = i
        
        if rib_no is None:
            raise ValueError(f"no rib found for node: {self}")

        return shape.get_point(rib_no, self.rib_pos)
