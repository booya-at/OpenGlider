from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Self

import euklid
import pydantic

from openglider.glider.cell.attachment_point import CellAttachmentPoint
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.lines import Line, LineSet, Node, line_types
from openglider.lines.lineset import LineTreePart
from openglider.utils.dataclass import BaseModel
from openglider.utils.table import Table
from openglider.vector.unit import Length

if TYPE_CHECKING:
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)

class LineSetTable(BaseModel):
    table: Table = pydantic.Field(default_factory=Table)
    lower_attachment_points: dict[str, Node] = pydantic.Field(default_factory=dict)

    def get_lineset(self, glider: Glider, v_inf: euklid.vector.Vector3D) -> LineSet:
        # upper -> dct {name: node}
        num_rows = self.table.num_rows
        num_cols = self.table.num_columns

        lines = []
        current_nodes: list[Node] = []
        row = 0
        column = 0

        while row < num_rows:
            value = self.table[row, column]  # length or node_no
            line_level = column // 2

            if value is None:
                if column == 0:
                    # if no lower node is defined, skip to line column (>=1)
                    column += 1
                elif column + 2 >= num_cols:
                    # reached the end of the table (does this even happen?)
                    row += 1
                    column = 0
                else:
                    # go one level up
                    column += 2

            if value is not None:
                if column == 0:  # lower nodes
                    lower_node_name = self.table[row, 0]
                    if not type(lower_node_name) == str:
                        lower_node_name = str(int(lower_node_name))
                    
                    attachment_point = self.lower_attachment_points[lower_node_name]
                    current_nodes = [attachment_point]
                    column += 1

                else:
                    # We have a line
                    line_type_name = str(self.table[row, column + 1])

                    if match := isinstance(value, str) and re.match(r"(.*)([+-].*)", value):
                        name_or_length = match.group(0)
                        trim_correction = Length(match.group(2))
                    else:
                        name_or_length = value
                        trim_correction = Length(0.)

                    if not len(current_nodes) > line_level:
                        raise ValueError()
                    current_nodes = current_nodes[:line_level+1]
                    lower_node = current_nodes[line_level]

                    upper: AttachmentPoint | CellAttachmentPoint | Node
                    # gallery
                    if column + 2 >= num_cols - 1 or self.table[row, column + 2] is None:
                        upper = glider.attachment_points[name_or_length]
                        line_length = None
                        row += 1
                        column = 0
                    # other line
                    else:
                        upper = Node(node_type=Node.NODE_TYPE.KNOT)
                        current_nodes.append(upper)
                        line_length = Length(name_or_length)
                        column += 2
                    
                    line_type_name_parts = line_type_name.split("#")
                    if len(line_type_name_parts) == 2:
                        line_type_name = line_type_name_parts[0]
                        color = line_type_name_parts[1]
                    else:
                        color = "default"

                    lines.append(Line(
                        lower_node=lower_node,
                        upper_node=upper,
                        v_inf=v_inf,
                        line_type=line_types.LineType.get(line_type_name),
                        target_length=line_length,
                        color=color,
                        trim_correction=trim_correction
                    ))

        return LineSet(lines, v_inf=v_inf)
    
    @classmethod
    def from_lineset(cls, lineset: LineSet) -> Self:
        line_tree = lineset.create_tree()
        table = Table()

        def insert_block(line: Line, upper: list[LineTreePart], row: int, column: int) -> int:
            if column == 0:
                table.set_value(0, row, line.lower_node.name)
                column += 1

            line_type_name = line.line_type.name
            if line.color:
                line_type_name += f"#{line.color}"
            
            length_correction = ""
            if line.trim_correction:
                length_correction = str(line.trim_correction)
                if not length_correction.startswith(("+", "-")):
                    length_correction = "+" + length_correction

            table.set_value(column+1, row, line_type_name)
            
            if upper:
                table.set_value(column, row, line.target_length)
                for line, line_upper in upper:
                    row = insert_block(line, line_upper, row, column+2)
            else:
                table.set_value(column, row, line.upper_node.name)
                row += 1

            return row

        row = 0
        for line, upper_lines in line_tree:
            row = insert_block(line, upper_lines, row, 0)
        
        lower_points = {
            n.name: n
            for n in lineset.lower_attachment_points
        }

        return cls(table=table, lower_attachment_points=lower_points)
    
    def scale(self, factor: float, scale_lower_floor: bool) -> Self:
        offset_2nd_level = 0
        for row in range(self.table.num_rows):
            column = 1
            while column < self.table.num_columns:
                if column + 2 < self.table.num_columns and self.table[row, column+2] and self.table[row, column]:
                    original_length = self.table[row, column]
                    scaled_length = original_length * factor

                    if column == 1 and not scale_lower_floor:
                        # riser offset
                        # riser_theoretical = riser_original * factor
                        # factor < 1 => riser remains longer than it should -> next floor should be shorter to compensate
                        offset_2nd_level = scaled_length - original_length
                    else:
                        if column == 3:
                            scaled_length += offset_2nd_level

                        self.table[row, column] = scaled_length
                    
                column += 2

        return self
