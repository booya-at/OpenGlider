import copy
import numpy

from openglider.glider.rib_elements import AttachmentPoint
from openglider.lines import Node, Line, LineSet


class LowerNode2D(object):
    """lower attachment point"""
    def __init__(self, pos, pos3D, nr=None):
        self.pos = pos
        self.pos3D = pos3D
        self.nr = nr

    def __json__(self):
        return{
            "pos": self.pos,
            "pos3D": self.pos3D,
            "nr": self.nr}

    @classmethod
    def __from_json__(cls, pos, pos3D, nr):
        p = cls(pos, pos3D)
        p.nr = nr
        return p

    def get_node(self, glider):
        return Node(node_type=0, position_vector=numpy.array(self.pos3D))


class UpperNode2D(object):
    """stores the 2d data of an attachment point"""
    def __init__(self, rib_no, position, force=1., nr=None):
        self.rib_no = rib_no
        self.position = position  # value from 0...100
        self.force = force
        self.nr = nr

    def __json__(self):
        return {'rib_no': self.rib_no,
                'position': self.position,
                'force': self.force,
                'nr': self.nr}

    def get_2d(self, glider_2d):
        _, front, back = glider_2d.shape()
        xpos = numpy.unique([i[0] for i in front if i[0] >= 0.])
        pos = self.position / 100.
        if self.rib_no < len(xpos):
            x = xpos[self.rib_no]
            j = self.rib_no + len(front) - len(xpos)
            chord = back[j][1] - front[j][1]
            y = front[j][1] + pos * chord
            return x, y

    def get_node(self, glider):
        node = AttachmentPoint(glider.ribs[self.rib_no], None,
                               self.position/100, [0, 0, self.force])
        node.get_position()
        return node


class BatchNode2D(object):
    def __init__(self, pos_2d, nr=None):
        self.pos_2d = pos_2d  # pos => 2d coordinates
        self.nr = nr

    def __json__(self):
        return{
            "pos_2d": self.pos_2d,
            "nr": self.nr
        }

    def get_node(self, glider):
        return Node(node_type=1)


class LineSet2D(object):
    def __init__(self, line_list, node_list):
        self.lines = line_list
        self.nodes = node_list

    def __json__(self):
        lines = [copy.copy(line) for line in self.lines]
        nodes = self.nodes
        print(self.nodes)
        for line in lines:
            line.upper_point = nodes.index(line.upper_point)
            line.lower_point = nodes.index(line.lower_point)
        return {"lines": lines,
                "nodes": nodes
        }

    @classmethod
    def __from_json__(cls, lines, nodes):
        lineset = cls(lines, nodes)
        nodes = lineset.nodes
        for line in lineset.lines:
            if isinstance(line.upper_point, int):
                line.upper_point = nodes[line.upper_point]
            if isinstance(line.lower_point, int):
                line.lower_point = nodes[line.lower_point]
        return lineset

    def return_lineset(self, glider):
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
            lower = line.lower_point.temp_node
            upper = line.upper_point.temp_node
            if lower and upper:
                line = Line(number=line_no, lower_node=lower, upper_node=upper,
                            vinf=glider.v_inf, target_length=line.target_length)
                lines.append(line)

        return LineSet(lines, glider.v_inf)

    def sort_lines(self, lower_att):
        """
        Recursive sorting of lines (check direction)
        """
        for line in self.lines:
            if not line.is_sorted:
                if lower_att == line.upper_point:
                    line.lower_point, line.upper_point = line.upper_point, line.lower_point
                if lower_att == line.lower_point:
                    line.is_sorted = True
                    self.sort_lines(line.upper_point)

    def delete_not_connected(self, glider):
        temp = []
        temp_new = []
        for line in self.lines:
            if isinstance(line.upper_point, UpperNode2D):
                if line.upper_point.rib_no >= len(glider.ribs):
                    temp.append(line)
                    self.nodes.remove(line.upper_point)

        while temp:
            for line in temp:
                conn_up_lines = [j for j in self.lines if (j.lower_point == line.lower_point and j != line)]
                conn_lo_lines = [j for j in self.lines if (j.upper_point == line.lower_point and j != line)]
                if len(conn_up_lines) == 0:
                    self.nodes.remove(line.lower_point)
                    self.lines.remove(line)
                    temp_new += conn_lo_lines
                temp.remove(line)
            temp = temp_new


class Line2D(object):
    def __init__(self, lower_node, upper_node, target_length=None):
        self.lower_node = lower_node
        self.upper_node = upper_node
        self.target_length = target_length
        self.is_sorted = False

    def __json__(self):
        return{
            "lower_node": self.lower_node,
            "upper_node": self.upper_node,
            "target_length": self.target_length,
            }