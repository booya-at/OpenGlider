from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import euklid
from openglider.glider.shape import Shape
from openglider.lines import Node
from openglider.utils.dataclass import dataclass
from openglider.vector.polygon import Circle, Ellipse

if TYPE_CHECKING:
    from openglider.glider.cell.cell import Cell
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)


class CellAttachmentPoint(Node):
    ballooned=False

    def __init__(self, name, cell_pos, rib_pos, force=None, offset=None, node_type=Node.NODE_TYPE.UPPER):
        super().__init__(node_type=Node.NODE_TYPE.UPPER, force=force)
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
            "cell_pos": self.cell_pos,
            "rib_pos": self.rib_pos,
            "name": self.name,
            "force": self.force
        }

    def get_position(self, cell: Cell) -> euklid.vector.Vector3D:
        ik = cell.rib1.profile_2d(self.rib_pos)

        if self.rib_pos in (-1, 1):
            p1 = cell.rib1.profile_3d.get(ik)
            p2 = cell.rib2.profile_3d.get(ik)
            self.vec = p1 + (p2 - p1)*self.cell_pos
        else:
            self.vec = cell.midrib(self.cell_pos, ballooning=self.ballooned)[ik]
        
        if not isinstance(self.force, euklid.vector.Vector3D):
            self.force = cell.get_normvector().normalized() * self.force
            
        return self.vec
    
    def get_position_2d(self, shape: Shape, glider: "Glider") -> euklid.vector.Vector2D:
        cell_no = None
        for i, cell in enumerate(glider.cells):
            if self in cell.attachment_points:
                cell_no = i

        return shape.get_point(cell_no+self.cell_pos, self.rib_pos)

