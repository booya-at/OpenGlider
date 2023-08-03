from __future__ import annotations
from typing import Any, Union, TYPE_CHECKING
from collections.abc import Mapping

import ast
import logging
import re

import euklid
from openglider.glider.cell.attachment_point import CellAttachmentPoint
from openglider.glider.cell.cell import Cell
from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.base import CellTable, Keyword, RibTable, dto
from openglider.glider.parametric.table.base.parser import Parser
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.glider.rib.rib import Rib
from openglider.utils.table import Table
from openglider.vector.unit import Length, Percentage

if TYPE_CHECKING:
    from openglider.glider.glider import Glider
    from openglider.glider.parametric.glider import ParametricGlider

logger = logging.getLogger(__name__)

class ATP(dto.DTO):
    name: str
    pos: Percentage
    force: float | str

    #@validator("force", pre=True)
    #def validate_force(self, force: Any):
    #    pass

    def get_object(self) -> AttachmentPoint:
        #raise NotImplementedError()
        logger.warning(f"get element {self}")
        return AttachmentPoint(
            rib_pos=self.pos,
            name=self.name,
        )


class ATPPROTO(ATP):
    protoloop_distance: Percentage | Length


class AttachmentPointTable(RibTable):
    regex_node_layer = re.compile(r"([a-zA-Z]*)([0-9]*)")

    keywords = {
        "ATP": Keyword([("name", str), ("pos", float), ("force", Union[float, str])], target_cls=AttachmentPoint), 
        "AHP": Keyword([("name", str), ("pos", float), ("force", Union[float, str])], target_cls=AttachmentPoint),
        "ATPPROTO": Keyword([("name", str), ("pos", float), ("force", Union[float, str]), ("proto_distance", float)], target_cls=AttachmentPoint)
    }
    dtos = {
        #"ATP": ATP,
        #"AHP": ATP,
    }

    def get_element(self, row: int, keyword: str, data: list[Any], resolvers: list[Parser]=None, rib: Rib=None, **kwargs: Any) -> AttachmentPoint:
        # rib_no, rib_pos, cell_pos, force, name, is_cell
        force = data[2]

        if isinstance(force, str):
            force = euklid.vector.Vector3D(ast.literal_eval(force))
        elif rib is not None:
            force = AttachmentPoint.calculate_force_rib_aligned(rib, force)

        assert resolvers is not None
        resolver = resolvers[row]
        rib_pos = resolver.parse(data[1])
        
        node = AttachmentPoint(name=data[0], rib_pos=rib_pos, force=force)  # type: ignore

        if keyword == "ATPPROTO":
            node.protoloops = 1

            default_resolver = Parser()
            node.protoloop_distance = default_resolver.parse(data[3])  # type: ignore
        
        return node
    
    def apply_forces(self, forces: Mapping[str, euklid.vector.Vector3D | float]) -> None:
        new_table = Table()

        for keyword_name, keyword in self.keywords.items():
            data_length = keyword.attribute_length
            for column in self.get_columns(self.table, keyword_name, data_length):
                for row in range(2, column.num_rows):
                    name = column[row, 0]
                    if name:
                        if name in forces:
                            force = forces[name]
                            try:
                                if isinstance(force, float):
                                    raise TypeError()
                                column[row, 2] = str(list(force))
                            except TypeError:
                                column[row, 2] = force
                        else:
                            logger.warning(f"no force for {name}")
                
                new_table.append_right(column)
        
        self.table = new_table
    
    @classmethod
    def from_glider(cls, glider: Glider) -> ParametricGlider:
        raise NotImplementedError()
        table = Table()

        layer_columns: dict[str, int] = {}

        for cell_no, cell in enumerate(glider.cells):
            #cell_layers = []
            attachment_points = cell.get_attachment_points(glider)
            for att_point in attachment_points:
                match = cls.regex_node_layer.match(att_point.name)
                
                if match:
                    layer = match.group(1)
                        
                    if layer not in layer_columns:
                        layer_columns[layer] = len(layer_columns)
                    
                    column_no = 2*layer_columns[layer]
                    table[cell_no+1, column_no] = att_point.name
                    table[cell_no+1, column_no+1] = att_point.pos
        
        return cls(table)                  
                    

class CellAttachmentPointTable(CellTable):
    keywords = {
        "ATP": Keyword([("name", str), ("cell_pos", float), ("rib_pos", float), ("force", Union[float, str])], target_cls=CellAttachmentPoint),
        "AHP": Keyword([("name", str), ("cell_pos", float), ("rib_pos", float), ("force", Union[float, str])], target_cls=CellAttachmentPoint),
        "ATPDIFF": Keyword([("name", str), ("cell_pos", float), ("rib_pos", float), ("force", Union[float, str]), ("offset", float)], target_cls=CellAttachmentPoint)
    }

    def get_element(self, row: int, keyword: str, data: list[Any], curves: dict[str, GliderCurveType]={}, cell: Cell=None, **kwargs: Any) -> CellAttachmentPoint:
        force = data[3]

        if isinstance(force, str):
            force = euklid.vector.Vector3D(ast.literal_eval(force))
        elif cell is not None:
            force = CellAttachmentPoint.calculate_force_cell_aligned(cell, force)


        node = CellAttachmentPoint(name=data[0], cell_pos=data[1], rib_pos=data[2], force=force)

        if len(data) > 4:
            offset = data[4]
            if isinstance(offset, str):
                offset = curves[offset].get(row)
            
            node.offset = offset

        return node

    def from_glider(self, glider: Glider) -> CellAttachmentPointTable:
        raise NotImplementedError()
