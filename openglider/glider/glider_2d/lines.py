import copy
import numpy

from openglider.glider.rib import AttachmentPoint
from openglider.lines import Node, Line, LineSet
from openglider.utils import recursive_getattr
from openglider.lines import line_types


class LowerNode2D(object):
    """lower attachment point"""
    def __init__(self, pos_2D, pos_3D, nr=None, layer=None):
        self.pos_2D = pos_2D
        self.pos_3D = pos_3D
        self.nr = nr
        self.layer = layer or "all"

    def __json__(self):
        return{
            "pos_2D": self.pos_2D,
            "pos_3D": self.pos_3D,
            "nr": self.nr,
            "layer": self.layer}

    def get_node(self, glider):
        return Node(node_type=0, position_vector=numpy.array(self.pos_3D))


class UpperNode2D(object):
    """stores the 2d data of an attachment point"""
    def __init__(self, rib_no, rib_pos, force=1., nr=None, layer=None):
        self.rib_no = rib_no
        self.rib_pos = rib_pos  # value from 0...1
        self.force = force
        self.nr = nr
        self.layer = layer or "all"

    def __json__(self):
        return {'rib_no': self.rib_no,
                'rib_pos': self.rib_pos,
                'force': self.force,
                'nr': self.nr,
                "layer": self.layer}

    def get_2d(self, glider_2d):
        # _, front, back = glider_2d.shape()                          # rib numbering convention???
        # xpos = numpy.unique([i[0] for i in front if i[0] >= 0.])
        front_back = glider_2d.ribs()[glider_2d.has_center_cell:]
        pos = self.rib_pos
        if self.rib_no <= len(front_back):
            rib_no = self.rib_no - glider_2d.has_center_cell
            fr, ba = front_back[rib_no]
            chord = ba[1] - fr[1]
            x = fr[0]
            y = fr[1] + pos * chord
            return x, y

    def get_node(self, glider):
        node = AttachmentPoint(glider.ribs[self.rib_no], None,
                               self.rib_pos, [0, 0, self.force])
        node.get_position()
        return node


class BatchNode2D(object):
    def __init__(self, pos_2D, nr=None, layer=None):
        self.pos_2D = pos_2D  # pos => 2d coordinates
        self.nr = nr
        self.layer = layer or "all"

    def __json__(self):
        return{
            "pos_2D": self.pos_2D,
            "nr": self.nr,
            "layer": self.layer
        }

    def get_node(self, glider):
        return Node(node_type=1)


class LineSet2D(object):
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

    def return_lineset(self, glider, v_inf):
        lines = []
        # first get the lowest points (lw-att)
        lowest = [node for node in self.nodes if isinstance(node, LowerNode2D)]
        # now get the connected lines
        # get the other point (change the nodes if necesarry)
        for node in lowest:
            self.sort_lines(node)
        self.delete_not_connected(glider)
        for node in self.nodes:
            node.temp_node = node.get_node(glider)  # store the nodes to remember them with the lines
        # set up the lines!
        for line_no, line in enumerate(self.lines):
            lower = line.lower_node.temp_node
            upper = line.upper_node.temp_node
            if lower and upper:
                line = Line(number=line_no, lower_node=lower, upper_node=upper,
                            vinf=v_inf, target_length=line.target_length,
                            line_type=line.line_type)
                lines.append(line)

        return LineSet(lines, v_inf)

    def set_default_nodes2d_pos(self, glider):
        lineset_3d = self.return_lineset(glider, [10,0,0])
        lineset_3d.calc_geo()
        line_dict = {line_no: line2d for
                     line_no, line2d in enumerate(self.lines)}

        for line in lineset_3d.lines:
            pos_2d = line.upper_node.vec
            line_dict[line.number].upper_node.pos_2D = [pos_2d[1], pos_2d[2]]



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

    def delete_not_connected(self, glider):
        temp = []
        temp_new = []
        for line in self.lines:
            if isinstance(line.upper_node, UpperNode2D):
                if line.upper_node.rib_no >= len(glider.ribs):
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
                 target_length=None, line_type='default', layer=None):
        self.lower_node = lower_node
        self.upper_node = upper_node
        self.target_length = target_length
        self.is_sorted = False
        self.line_type = line_types.LineType.get(line_type)
        self.layer = layer or "all"

    def __json__(self):
        return{
            "lower_node": self.lower_node,
            "upper_node": self.upper_node,
            "target_length": self.target_length,
            "line_type": self.line_type.name
            }