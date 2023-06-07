from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Any

import euklid
from openglider.glider.shape import Shape
from openglider.lines.node import Node, NODE_TYPE_ENUM
from openglider.vector.unit import Percentage

if TYPE_CHECKING:
    from openglider.glider.cell.cell import Cell
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)


class CellAttachmentPoint(Node):
    cell_pos: float
    rib_pos: Percentage
    node_type: NODE_TYPE_ENUM = Node.NODE_TYPE.UPPER
    ballooned=False
    offset: float = 0.

    def __repr__(self) -> str:
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self) -> Dict[str, Any]:
        return {
            "cell_pos": self.cell_pos,
            "rib_pos": self.rib_pos,
            "name": self.name,
            "force": self.force
        }
    
    @classmethod
    def __from_json__(cls, **kwargs: Any) -> CellAttachmentPoint:
        force = euklid.vector.Vector3D(kwargs.pop("force"))
        return cls(**kwargs, force=force)

    @classmethod
    def calculate_force_cell_aligned(cls, cell: Cell, force: float) -> euklid.vector.Vector3D:
        return cell.get_normvector() * force

    def get_position(self, cell: Cell) -> euklid.vector.Vector3D:
        ik = cell.rib1.profile_2d(self.rib_pos)

        if self.rib_pos in (-1, 1):
            p1 = cell.rib1.profile_3d.get(ik)
            p2 = cell.rib2.profile_3d.get(ik)
            self.position = p1 + (p2 - p1)*self.cell_pos
        else:
            self.position = cell.midrib(self.cell_pos, ballooning=self.ballooned)[ik]
        
        if not isinstance(self.force, euklid.vector.Vector3D):
            self.force = cell.get_normvector().normalized() * self.force
            
        return self.position
    
    def get_position_2d(self, shape: Shape, glider: "Glider") -> euklid.vector.Vector2D:
        cell_no = None
        for i, cell in enumerate(glider.cells):
            if self in cell.attachment_points:
                cell_no = i
        
        if cell_no is None:
            raise ValueError("Not in a cell: {self}")

        return shape.get_point(cell_no+self.cell_pos, self.rib_pos.si)

