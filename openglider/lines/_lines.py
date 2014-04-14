#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.

from _functions import *
from _elements import Line, Node, LinePar
from openglider.vector import normalize
import numpy
import openglider.graphics as g


class Lines():

    def __init__(self):
        self.calc_par = {}
        self.line_types = {}
        self.nodes = {}
        self.lines = []

    def calc_geo(self, lines):
        for l in lines:
            if self.nodes[l.upper_node].type == 1:
                vec_0 = self.nodes[l.lower_node].vec
                t = self.get_tangential_comp(l, vec_0)
                self.nodes[l.upper_node].vec = vec_0 + t * l.length
                conn_lines = self.get_connected_lines(l.upper_node)
                self.calc_geo(conn_lines)

    def calc_sag(self):
        #1 evere line calculates its matrix entries (pos+value) + entry for rhs
        #2 solve matrix
        #3 save sag cooef
        pass

    def calc_stretch(self):
        pass

    def get_tangential_comp(self, line, pos_vec):
        upper_node_nr = []
        flatten(self.get_upper_influence_node(line), upper_node_nr)
        tangent = numpy.array([0., 0., 0.])
        for node_nr in upper_node_nr:
            tangent += self.nodes[node_nr].calc_force_infl(pos_vec)
        return(normalize(tangent))

    def get_upper_influence_node(self, line):
        upper_node = self.nodes[line.upper_node]
        conn_l = self.get_connected_lines(upper_node.number)
        if len(conn_l) == 0:
            return(upper_node.number)
        else:
            return(map(self.get_upper_influence_node, conn_l))

    def get_connected_lines(self, node_number):
        ret = []
        for l in self.lines:
            if l.lower_node == node_number:
                ret.append(l)
        return(ret)

    def get_lowest_lines(self):
        ret = []
        for l in self.lines:
            n = self.nodes[l.lower_node]
            if n.type == 0:
                ret.append(l)
        return(ret)

    def import_lines(self, path):
        key_dict = {
            "NODES": [8, self.store_nodes],
            "LINES": [5, self.store_lines],
            "LINEPAR": [4, self.store_line_par],
            "CALCPAR": [3, self.store_calc_par]
        }
        import_file(path, key_dict)
        self.set_line_par()

    def store_nodes(self, values):
        n = Node(try_convert(values[0], int))
        n.type = try_convert(values[1], int)
        n.vec = map(lambda x: try_convert(x, float), values[2:5])
        n.force = map(lambda x: try_convert(x, float), values[5:8])
        self.nodes[n.number] = n

    def store_lines(self, values):
        l = Line(try_convert(values[0], int))
        l.lower_node = try_convert(values[1], int)
        l.upper_node = try_convert(values[2], int)
        l.length = try_convert(values[3], float)
        l.type = values[4]
        self.lines.append(l)

    def store_line_par(self, values):
        lp = LinePar(values[0])
        lp.cw = try_convert(values[1], float)
        lp.b = try_convert(values[2], float)
        lp.strech = try_convert(values[3], float)
        self.line_types[lp.type] = lp

    def store_calc_par(self, values):
        self.calc_par["GEOSTEPS"] = values[0]
        self.calc_par["SAGSTEPS"] = values[1]
        self.calc_par["ITER"] = values[2]

    def set_line_par(self):
        for l in self.lines:
            name = l.type
            l.cw = self.line_types[name].cw
            l.b = self.line_types[name].b
            l.strech_factor = self.line_types[name].strech

    def visual_output(self):
        lines = [[self.nodes[l.lower_node].vec, self.nodes[l.upper_node].vec]
                 for l in self.lines]
        lines_proj = [[self.nodes[l.lower_node].vec_proj, self.nodes[l.upper_node].vec_proj]
                      for l in self.lines]
        g.Graphics3D(map(g.Line, lines + lines_proj))


if __name__ == "__main__":
    lines = Lines()
    lines.import_lines("TEST_INPUT_FILE.txt")
    strt = lines.get_lowest_lines()
    lines.calc_geo(strt)
    for n in lines.nodes.values():
        n.calc_proj_vec([1, 1, 1])
    lines.visual_output()
