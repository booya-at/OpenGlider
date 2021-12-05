from typing import Dict
import ast
import logging
import re

import euklid
import openglider
from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable, Keyword

from openglider.glider.parametric.lines import UpperNode2D

logger = logging.getLogger(__name__)

class AttachmentPointTable(ElementTable):
    regex_node_layer = re.compile(r"([a-zA-Z]*)([0-9]*)")

    keywords = {
        "ATP": Keyword(["name", "pos", "force"]), 
        "AHP": Keyword(["name", "pos", "force"]),
        "ATPPROTO": Keyword(["name", "pos", "force", "proto_distance"])
    }

    def get_element(self, row, keyword, data, curves={}, **kwargs) -> UpperNode2D:
        # rib_no, rib_pos, cell_pos, force, name, is_cell
        force = data[2]

        if isinstance(force, str):
            force = ast.literal_eval(force)

        rib_pos = data[1]
        if isinstance(rib_pos, str):
            rib_pos = curves[rib_pos].get(row)
            
        node = UpperNode2D(row, rib_pos, 0, force, name=data[0], is_cell=False)

        if keyword == "ATPPROTO":
            node.proto_dist = data[3]
        
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
    def from_glider(cls, glider: "openglider.glider.Glider"):
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

                    
                    

class CellAttachmentPointTable(ElementTable):
    keywords = {
        "ATP": Keyword(["name", "cell_pos", "rib_pos", "force"]), 
        "ATPDIFF": Keyword(["name", "cell_pos", "rib_pos", "force", "offset"]), 
        "AHP": Keyword(["name", "cell_pos", "rib_pos", "force"]),
    }

    def get_element(self, row, keyword, data, curves={}, **kwargs) -> UpperNode2D:
        force = data[3]

        if isinstance(force, str):
            force = ast.literal_eval(force)

        node = UpperNode2D(row, data[2], data[1], force, name=data[0], is_cell=True)

        if len(data) > 4:
            offset = data[4]
            if isinstance(offset, str):
                offset = curves[offset].get(row)
            
            node.offset = offset

        return node

