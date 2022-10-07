from __future__ import annotations
from typing import Dict, Union, TYPE_CHECKING

import ast
import logging
import re

import euklid
from openglider.glider.cell.attachment_point import CellAttachmentPoint
from openglider.glider.parametric.table.elements import CellTable, Keyword, RibTable
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.utils.table import Table

if TYPE_CHECKING:
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)

class AttachmentPointTable(RibTable):
    regex_node_layer = re.compile(r"([a-zA-Z]*)([0-9]*)")

    keywords = {
        "ATP": Keyword([("name", str), ("pos", float), ("force", Union[float, str])], target_cls=AttachmentPoint), 
        "AHP": Keyword([("name", str), ("pos", float), ("force", Union[float, str])], target_cls=AttachmentPoint),
        "ATPPROTO": Keyword([("name", str), ("pos", float), ("force", Union[float, str]), ("proto_distance", float)], target_cls=AttachmentPoint)
    }

    def get_element(self, row, keyword, data, curves={}, **kwargs) -> AttachmentPoint:
        # rib_no, rib_pos, cell_pos, force, name, is_cell
        force = data[2]

        if isinstance(force, str):
            force = ast.literal_eval(force)
            try:
                force = euklid.vector.Vector3D(force)
            except Exception:
                pass

        rib_pos = data[1]
        if isinstance(rib_pos, str):
            rib_pos = curves[rib_pos].get(row)
        
        node = AttachmentPoint(name=data[0], rib_pos=rib_pos, force=force)

        if keyword == "ATPPROTO":
            node.protoloop_distance_absolute = data[3]
            node.protoloops = 1
        
        return node
    
    def apply_forces(self, forces: Dict[str, euklid.vector.Vector3D]):
        new_table = Table()

        for keyword_name, keyword in self.keywords.items():
            data_length = keyword.attribute_length
            for column in self.get_columns(self.table, keyword_name, data_length):
                for row in range(1, column.num_rows):
                    name = column[row, 0]
                    if name:
                        if name in forces:
                            column[row, 2] = str(list(forces[name]))
                        else:
                            logger.warning(f"no force for {name}")
                
                new_table.append_right(column)
        
        self.table = new_table
    
    @classmethod
    def from_glider(cls, glider: Glider):
        raise NotImplementedError()
        table = Table()

        layer_columns: Dict[str, int] = {}

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

    def get_element(self, row, keyword, data, curves={}, **kwargs) -> CellAttachmentPoint:
        force = data[3]

        if isinstance(force, str):
            force = ast.literal_eval(force)

        node = CellAttachmentPoint(name=data[0], cell_pos=data[1], rib_pos=data[2], force=force)

        if len(data) > 4:
            offset = data[4]
            if isinstance(offset, str):
                offset = curves[offset].get(row)
            
            node.offset = offset

        return node

    def from_glider(self, glider: Glider):
        raise NotImplementedError()
