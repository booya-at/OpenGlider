import copy
import re
import ast
import numpy as np
import logging

from openglider.glider.rib.elements import AttachmentPoint, CellAttachmentPoint
from openglider.lines import Node, Line, LineSet
from openglider.utils import recursive_getattr
from openglider.lines import line_types
from openglider.utils.table import Table

logger = logging.getLogger(__name__)

class LowerNode2D(object):
    """lower attachment point"""
    def __init__(self, pos_2D, pos_3D, name="unnamed", layer=None):
        self.pos_2D = pos_2D
        self.pos_3D = pos_3D
        self.name = name
        self.layer = layer or ""

    def __repr__(self):
        return "<LowerNode2D {}>".format(self.name)

    def __json__(self):
        return{
            "pos_2D": self.pos_2D,
            "pos_3D": self.pos_3D,
            "name": self.name,
            "layer": self.layer}

    def get_2D(self, *args):
        return self.pos_2D

    def get_node(self, glider):
        return Node(node_type=0, position_vector=np.array(self.pos_3D), name=self.name)


class UpperNode2D(object):
    """stores the 2d data of an attachment point"""
    def __init__(self, cell_no, rib_pos, cell_pos=0, force=1., name="unnamed", layer=None):
        self.cell_no = cell_no
        self.cell_pos = cell_pos
        self.rib_pos = rib_pos  # value from 0...1
        self.force = force
        self.name = name
        self.layer = layer or ""

    def __json__(self):
        return {'cell_no': self.cell_no,
                'rib_pos': self.rib_pos,
                "cell_pos": self.cell_pos,
                'force': self.force,
                'name': self.name,
                "layer": self.layer}

    def __repr__(self):
        return "<UpperNode2D name:{} cell_no:{} cell_pos: {} rib_pos:{}".format(self.name, self.cell_no, self.cell_pos, self.rib_pos)

    def get_2D(self, parametric_shape):
        x = self.cell_no + self.cell_pos + parametric_shape.has_center_cell
        
        return parametric_shape.get_shape_point(x, self.rib_pos)

    def get_node(self, glider):
        if 1 > self.cell_pos > 0: # attachment point between two ribs
            cell = glider.cells[self.cell_no + glider.has_center_cell]
            if isinstance(self.force, (list, tuple, np.ndarray)):
                force = list(self.force)
            else:
                force = cell.get_normvector() * self.force

            node = CellAttachmentPoint(cell, self.name, self.cell_pos, self.rib_pos, force)
        else: # attachment point on the rib
            rib = glider.ribs[self.cell_no + self.cell_pos + glider.has_center_cell]
            if isinstance(self.force, (list, tuple, np.ndarray)):
                force = list(self.force)
            else:
                force = rib.rotation_matrix.apply([0, self.force, 0])

            node = AttachmentPoint(rib, self.name, self.rib_pos, force)

        node.get_position()
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
        return Node(node_type=1)

    def get_2D(self, *args):
        return self.pos_2D


class LineSet2D(object):
    regex_node = re.compile(r"([a-zA-Z]*)([0-9]*)")
    def __init__(self, line_list):
        self.lines = line_list

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

        return list(nodes)

    def get_upper_nodes(self, rib_no=None):
        nodes = set()
        for line in self.lines:
            node = line.upper_node
            if isinstance(node, UpperNode2D):
                if rib_no is None or node.cell_no == rib_no:
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
                            v_inf=None, target_length=line.target_length,
                            line_type=line.line_type, name=line.name)
                lines.append(line)

        return LineSet(lines, v_inf)

    def scale_forces(self, glider, node, weight):
        '''
        scales all forces to match a certain weight in a node
        '''
        # get upper connected force of the node
        # use z-direction of this force
        # compute scaling
        # scale all forces
        pass


    def scale(self, factor, scale_lower_floor=True):
        lower_nodes = self.get_lower_attachment_points()
        for line in self.lines:
            target_length = getattr(line, "target_length", None)
            if target_length is not None:
                if scale_lower_floor or line.lower_node not in lower_nodes:
                    line.target_length *= factor
        for node in lower_nodes:
            node.pos_3D = np.array(node.pos_3D) * factor
            node.pos_2D = np.array(node.pos_2D) * factor

    def set_default_nodes2d_pos(self, glider):
        lineset_3d = self.return_lineset(glider, [10,0,0])
        lineset_3d._calc_geo()
        line_dict = {line_no: line2d for
                     line_no, line2d in enumerate(self.lines)}

        for line in lineset_3d.lines:
            pos_3d = line.upper_node.vec
            pos_2d = [pos_3d[1], pos_3d[2]+0.2*pos_3d[0]]
            line_dict[line.number].upper_node.pos_2D = pos_2d

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

    def get_upper_connected_lines(self, node):
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

        def sort_key(line):
            nodes = get_influence_nodes(line)
            if not nodes:
                pass
                #return -1
            val = sum([100*(node.cell_no+node.cell_pos)+100*node.rib_pos for node in nodes])/len(nodes)
            
            return val

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
    def read_input_table(cls, sheet, attachment_points_lower, attachment_points_upper):

        # upper -> dct {name: node}
        num_rows = sheet.num_rows
        num_cols = sheet.num_columns

        linelist = []
        current_nodes = [None for row in range(num_cols)]
        row = 0
        column = 0
        count = 0

        while row < num_rows:
            value = sheet[row, column]  # length or node_no

            if value:
                if column == 0:  # first (line-)floor
                    lower_node_name = sheet[row, 0]
                    if not type(lower_node_name) == str:
                        lower_node_name = str(int(lower_node_name))
                    
                    current_nodes = [attachment_points_lower[lower_node_name]] + \
                                    [None for __ in range(num_cols)]
                    column += 1

                else:
                    # We have a line
                    line_type_name = sheet[row, column + 1]

                    lower_node = current_nodes[column // 2]

                    # gallery
                    if column + 2 >= num_cols - 1 or sheet[row, column + 2] is None:

                        upper = attachment_points_upper[value]
                        line_length = None
                        row += 1
                        column = 0
                    # other line
                    else:
                        upper = BatchNode2D([0, 0])
                        current_nodes[column // 2 + 1] = upper
                        line_length = sheet[row, column]
                        column += 2

                    linelist.append(
                        Line2D(lower_node, upper, target_length=line_length, line_type=line_type_name))
                    count += 1

            else:
                if column == 0:
                    column += 1
                elif column + 2 >= num_cols:
                    row += 1
                    column = 0
                else:
                    column += 2

        return cls(linelist)

    def get_attachment_point_table(self):
        nodes = self.get_upper_nodes()
        node_groups = {}
        num_cells = 0
        tables_cell = []
        tables_rib = []
        tables = []

        # sort by layer
        for node in nodes:
            match = self.regex_node.match(node.name)
            if match:
                layer_name = match.group(1)
            else:
                layer_name = "none"

            node_groups.setdefault(layer_name, [])
            node_groups[layer_name].append(node)
            num_cells = max(num_cells, node.cell_no)+1  # WHAT?

        groups = list(node_groups.keys())

        # per layer table
        def sorted(x):
            res = 0
            for i, character in enumerate(x[::-1]):
                res += (26**i)*(ord(character)-64)

            return res

        groups.sort(key=sorted)
        for key in groups:
            table = Table()
            group_nodes = node_groups[key]
            is_rib_attachment_point = all(n.cell_pos in (0, 1) for n in group_nodes)

            if is_rib_attachment_point:
                for rib_no in range(num_cells+1):
                    rib_nodes = filter(lambda n: n.cell_no+n.cell_pos == rib_no, group_nodes)

                    for i, node in enumerate(rib_nodes):
                        # name, rib_pos, force
                        table[0, 3*i] = "ATP"
                        table[rib_no+1, 3*i] = node.name
                        table[rib_no+1, 3*i+1] = node.rib_pos
                        table[rib_no+1, 3*i+2] = node.force
                
                tables_rib.append(table)

            else:
                for cell_no in range(num_cells):
                    cell_nodes = filter(lambda n: n.cell_no == cell_no, group_nodes)
                    for i, node in enumerate(cell_nodes):
                        # name, cell_pos, rib_pos, force
                        table[0, 4*i] = "ATP"
                        table[cell_no+1, 4*i] = node.name
                        table[cell_no+1, 4*i+1] = node.cell_pos
                        table[cell_no+1, 4*i+2] = node.rib_pos
                        table[cell_no+1, 4*i+3] = node.force

                tables_cell.append(table)

        total_table = Table()
        for table in tables_cell:
            total_table.append_right(table)

        total_table_ribs = Table()
        for table in tables_rib:
            total_table_ribs.append_right(table)
        return total_table_ribs, total_table
    
    @staticmethod
    def read_attachment_point_table(cell_table: Table=None, rib_table:Table=None, half_cell_no=None):
        has_center_cell=False
        if half_cell_no is not None:
            has_center_cell = half_cell_no % 2

        attachment_points = []
        values = ("name", "cell_pos", "rib_pos", "force")
        num_columns = int(cell_table.num_columns / 4)

        def get_force(force):
            if isinstance(force, str):
                return ast.literal_eval(force)
            return force
        
        for column in range(num_columns):
            column_0 = column*4
            assert cell_table[0, column_0] in ("ATP", "AHP")

            for row in range(1, cell_table.num_rows):
                name = cell_table[row, column_0]
                if name:
                    force = get_force(cell_table[row, column_0+3])
                    
                    cell_no = row - 1
                    if has_center_cell:
                        cell_no -= 1

                    attachment_points.append(UpperNode2D(
                        cell_no=cell_no,
                        name=name,
                        cell_pos = cell_table[row, column_0+1],
                        rib_pos = cell_table[row, column_0+2],
                        force=force # parse list/tuple
                        ))
        
        for column in range(int(rib_table.num_columns / 3)):
            for row in range(1, rib_table.num_rows):
                name = rib_table[row, column*3]
                if name:
                    rib_no = row-1
                    
                    rib_pos = rib_table[row, column*3+1]
                    force = get_force(rib_table[row, column*3+2])

                    attachment_points.append(UpperNode2D(
                        name=name,
                        cell_no=rib_no,
                        rib_pos=rib_pos,
                        force=force
                    ))
        

        for attachment_point in attachment_points:
            if attachment_point.cell_no >= half_cell_no:
                attachment_point.cell_no -= 1
                attachment_point.cell_pos = 1

        
        return attachment_points

    def delete_not_connected(self, glider):
        temp = []
        temp_new = []
        for line in self.lines:
            if isinstance(line.upper_node, UpperNode2D):
                if line.upper_node.cell_no >= len(glider.ribs):
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