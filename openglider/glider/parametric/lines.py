from __future__ import annotations

from typing import TYPE_CHECKING, Any, Tuple, List, Dict
import copy
import re
import logging
import math

import numpy as np
import euklid

from openglider.lines import Node, Line, LineSet
from openglider.utils import sign
from openglider.utils.dataclass import dataclass
from openglider.lines import line_types
from openglider.utils.table import Table

if TYPE_CHECKING:
    from openglider.glider.glider import Glider

logger = logging.getLogger(__name__)

class LowerNode2D(object):
    """lower attachment point"""
    def __init__(self, pos_2D, pos_3D, name="unnamed"):
        self.pos_2D = pos_2D
        self.pos_3D = pos_3D
        self.name = name

    def __repr__(self):
        return "<LowerNode2D {}>".format(self.name)

    def __json__(self):
        return{
            "pos_2D": self.pos_2D,
            "pos_3D": self.pos_3D,
            "name": self.name
        }

    def get_2D(self, *args):
        return self.pos_2D

    def get_node(self, glider):
        return Node(node_type=Node.NODE_TYPE.LOWER, position=self.pos_3D, name=self.name)


@dataclass
class UpperNode2D:
    name: str

    def __repr__(self):
        return f"<UpperNode2D name:{self.name}>"
    
    def __hash__(self) -> int:
        return hash(self.name)

    def get_2D(self, parametric_shape):
        return parametric_shape.get_shape_point(0, 0.5)

    def get_node(self, glider: Glider):
        node = glider.attachment_points[self.name]

        return node


class BatchNode2D(object):
    def __init__(self, pos_2D, name=None, layer=None):
        self.pos_2D = pos_2D  # pos => 2d coordinates
        self.name = name
        self.layer = layer or ""

    def __json__(self):
        return{
            "pos_2D": self.pos_2D,
            "name": self.name,
            "layer": self.layer
        }

    def get_node(self, glider):
        return Node(node_type=Node.NODE_TYPE.KNOT)

    def get_2D(self, *args):
        return self.pos_2D


class LineSet2D(object):
    trim_corrections: Dict[str, float]

    regex_node = re.compile(r"([a-zA-Z]*)([0-9]*)")

    def __init__(self, line_list, trim_corrections=None):
        self.lines = line_list
        self.trim_corrections = trim_corrections or {}

    def __json__(self):
        lines = [copy.copy(line) for line in self.lines]
        nodes = self.nodes
        for line in lines:
            line.upper_node = nodes.index(line.upper_node)
            line.lower_node = nodes.index(line.lower_node)
        return {"lines": lines,
                "nodes": nodes}

    @classmethod
    def __from_json__(cls, lines, nodes):
        lineset = cls(lines)
        for line in lineset.lines:
            if isinstance(line.upper_node, int):
                line.upper_node = nodes[line.upper_node]
            if isinstance(line.lower_node, int):
                line.lower_node = nodes[line.lower_node]
        return lineset

    @property
    def nodes(self):
        nodes = set()
        for line in self.lines:
            nodes.add(line.upper_node)
            nodes.add(line.lower_node)

            if line.upper_node is None:
                raise ValueError(f"upper node is None: {line.name} / {line.line_type}")
            if line.lower_node is None:
                raise ValueError(f"lower node is None: {line.name} / {line.line_type}")

        return list(nodes)

    def get_upper_nodes(self, rib_no=None) -> List[UpperNode2D]:
        nodes = set()
        for line in self.lines:
            node = line.upper_node
            if isinstance(node, UpperNode2D):
                nodes.add(line.upper_node)

        return list(nodes)

    def get_upper_node(self, name):
        for node in self.get_upper_nodes():
            if node.name == name:
                return node

    def get_lower_attachment_points(self):
        return [node for node in self.nodes if isinstance(node, LowerNode2D)]

    def return_lineset(self, glider, v_inf):
        """
        Get Lineset_3d
        :param glider: Glider3D
        :param v_inf:
        :return: LineSet (3d)
        """
        #v_inf = v_inf or glider.v_inf
        lines = []
        # now get the connected lines
        # get the other point (change the nodes if necessary)
        for node in self.get_lower_attachment_points():
            self.sort_lines(node)
        self.delete_not_connected(glider)

        logger.info("get nodes")

        nodes_3d = {node: node.get_node(glider) for node in self.nodes}
        # set up the lines!
        logger.info("get lines")
        for line_no, line in enumerate(self.lines):
            lower = nodes_3d[line.lower_node]
            upper = nodes_3d[line.upper_node]
            if lower and upper:
                line = Line(number=line_no, lower_node=lower, upper_node=upper,
                            v_inf=v_inf, target_length=line.target_length,
                            line_type=line.line_type, name=line.name)
                lines.append(line)

        lineset = LineSet(lines, v_inf)
        lineset.trim_corrections = self.trim_corrections.copy()

        return lineset

    def scale(self, factor, scale_lower_floor=True, scale_y=False):
        lower_nodes = []

        if not scale_lower_floor:
            lower_nodes = [n for n in self.get_lower_attachment_points() if "main" in n.name]
            if len(lower_nodes) < 1:
                lower_nodes = self.get_lower_attachment_points()
                if len(lower_nodes) < 1:
                    raise ValueError("There are no lower floor nodes")
            
        lower_nodes_offset = 0
        lower_lines_count = 0

        for line in self.lines:
            target_length = getattr(line, "target_length", None)
            if target_length is not None:
                if scale_lower_floor or line.lower_node not in lower_nodes:
                    line.target_length *= factor
                else:
                    lower_nodes_offset += line.target_length * (1-factor)
                    lower_lines_count += 1
        
        if lower_lines_count != 0:
            lower_nodes_offset /= lower_lines_count

        for node in self.get_lower_attachment_points():
            node.pos_3D[0] = node.pos_3D[0] * factor
            if scale_y:
                node.pos_3D[1] = node.pos_3D[1] * factor
            node.pos_3D[2] = node.pos_3D[2] * factor + sign(node.pos_3D[2]) * lower_nodes_offset
            #node.pos_2D = node.pos_2D * (factor + lower_nodes_offset / node.pos_2D.length())

    def set_default_nodes2d_pos(self, parametricshape):
        def get_node_pos(node) -> euklid.vector.Vector2D:
            if isinstance(node, UpperNode2D):
                return node.get_2D(parametricshape)
            
            nodes = [line.upper_node for line in self.get_upper_connected_lines(node)]

            if len(nodes) == 0:
                raise ValueError(f"no upper nodes for node {node}, {type(node)}, {UpperNode2D}")
            elif len(nodes) == 1:
                position = get_node_pos(nodes[0])
                node.pos_2D = position + euklid.vector.Vector2D([0, -0.2])
                return position

            node_positions = [get_node_pos(node) for node in nodes]

            position = sum(node_positions, euklid.vector.Vector2D()) * (1/len(node_positions))

            direction = euklid.vector.Vector2D()

            for node_pos in node_positions:
                diff = node_pos - position

                if diff.dot(euklid.vector.Vector2D([1, -1])) < 0:
                    direction += diff * -1
                else:
                    direction += diff
            
            rotation = euklid.vector.Rotation2D(-math.pi/2)
            direction.normalized()
            
            position += rotation.apply(direction.normalized()*0.1)

            node.pos_2D = position

            return position
        
        for node in self.get_lower_attachment_points():
            get_node_pos(node)

    def sort_lines(self, lower_att):
        """
        Recursive sorting of lines (check direction)
        """
        for line in self.lines:
            if not line.is_sorted:
                if lower_att == line.upper_node:
                    line.lower_node, line.upper_node = line.upper_node, line.lower_node
                if lower_att == line.lower_node:
                    line.is_sorted = True
                    self.sort_lines(line.upper_node)

    def get_upper_connected_lines(self, node: Node) -> List[Line]:
        return [line for line in self.lines if line.lower_node is node]

    def get_lower_connected_lines(self, node):
        return [line for line in self.lines if line.upper_node is node]

    def get_influence_nodes(self, line):
        if isinstance(line.upper_node, UpperNode2D):
            return [line.upper_node]
        return sum([self.get_influence_nodes(l) for l in self.get_upper_connected_lines(line.upper_node)], [])

    def create_tree(self, start_node=None):
        """
        Create a tree of lines
        :return: [(line, [(upper_line1, []),...]),(...)]
        """
        if start_node is None:
            start_node = self.get_lower_attachment_points()
            lines = []
            for node in start_node:
                lines += self.get_upper_connected_lines(node)
        else:
            lines = self.get_upper_connected_lines(start_node)

        def get_influence_nodes(line):
            if isinstance(line.upper_node, UpperNode2D):
                return [line.upper_node]
            return sum([get_influence_nodes(l) for l in self.get_upper_connected_lines(line.upper_node)], [])

        for line in lines:
            if not get_influence_nodes(line):
                return line

        def sort_key(line) -> Any:
            nodes = get_influence_nodes(line)
            if not nodes:
                pass
                #return -1
            
            layers = set()
            min_index = 99999

            for node in nodes:
                match = re.match(r"([a-zA-Z]+)([0-9]+)", node.name)
                if not match:
                    raise ValueError(f"invalid node name: {node.name}")
                
                layer, index = match.groups()
                layers.add(layer)
                min_index = min(int(index), min_index)
            
            return "".join(layers) + f"{min_index:09d}"

        lines.sort(key=sort_key)

        return [(line, self.create_tree(line.upper_node)) for line in lines]

    def get_input_table(self):
        table = Table()

        def insert_block(line, upper, row, column):
            table[row, column+1] = line.line_type.name
            if upper:
                table[row, column] = round(line.target_length, 3)
                for line, line_upper in upper:
                    row = insert_block(line, line_upper, row, column+2)
            else:  # Insert a top node
                name = line.upper_node.name
                if not name:
                    name = "Rib_{}/{}".format(line.upper_node.rib_no,
                                              line.upper_node.rib_pos)
                table[row, column] = name
                row += 1
            return row

        row = 0
        for node in self.get_lower_attachment_points():
            tree = self.create_tree(node)
            table[row, 0] = node.name
            for line, upper in tree:
                row = insert_block(line, upper, row, 1)

        return table

    @classmethod
    def read_input_table(cls, sheet, attachment_points_lower):

        # upper -> dct {name: node}
        num_rows = sheet.num_rows
        num_cols = sheet.num_columns

        linelist = []
        current_nodes = [None for row in range(num_cols)]
        row = 0
        column = 0

        while row < num_rows:
            value = sheet[row, column]  # length or node_no

            if value is not None:
                if column == 0:  # first (line-)floor
                    lower_node_name = sheet[row, 0]
                    if not type(lower_node_name) == str:
                        lower_node_name = str(int(lower_node_name))
                    
                    lower_node = attachment_points_lower[lower_node_name]
                    current_nodes.clear()
                    current_nodes.append(lower_node)
                    current_nodes +=  [None for __ in range(num_cols)]
                    column += 1

                else:
                    # We have a line
                    line_type_name = sheet[row, column + 1]

                    lower_node = current_nodes[column // 2]

                    # gallery
                    if column + 2 >= num_cols - 1 or sheet[row, column + 2] is None:
                        upper = UpperNode2D(value)
                        line_length = None
                        row += 1
                        column = 0
                    # other line
                    else:
                        upper = BatchNode2D([0, 0])
                        current_nodes[column // 2 + 1] = upper
                        line_length = sheet[row, column]
                        column += 2
                    
                    if lower_node is None:
                        logger.error(f"no lower_node: {row}/{column}")

                    linelist.append(
                        Line2D(lower_node, upper, target_length=line_length, line_type=line_type_name))
                        
            else:
                if column == 0:
                    column += 1
                elif column + 2 >= num_cols:
                    row += 1
                    column = 0
                else:
                    column += 2

        return cls(linelist)

    def delete_not_connected(self, glider: Glider):
        temp = []
        temp_new = []
        attachment_points = glider.attachment_points
        for line in self.lines:
            if isinstance(line.upper_node, UpperNode2D):
                if line.upper_node.name not in attachment_points:
                    temp.append(line)
                    self.nodes.remove(line.upper_node)

        while temp:
            for line in temp:
                conn_up_lines = [j for j in self.lines if (j.lower_node == line.lower_node and j != line)]
                conn_lo_lines = [j for j in self.lines if (j.upper_node == line.lower_node and j != line)]
                if len(conn_up_lines) == 0:
                    self.nodes.remove(line.lower_node)
                    self.lines.remove(line)
                    temp_new += conn_lo_lines
                temp.remove(line)
            temp = temp_new


class Line2D(object):
    def __init__(self, lower_node, upper_node, 
                 target_length=None, line_type='default', layer=None, name=None):
        self.lower_node = lower_node
        self.upper_node = upper_node
        self.target_length = target_length
        self.is_sorted = False
        self.line_type = line_types.LineType.get(line_type)
        self.layer = layer or ""
        self.name = name


    def __json__(self):
        return{
            "lower_node": self.lower_node,
            "upper_node": self.upper_node,
            "target_length": self.target_length,
            "line_type": self.line_type.name,
            "layer": self.layer,
            "name": self.name
            }
