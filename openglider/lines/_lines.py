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


import numpy
import openglider.graphics as g
from _functions import *
from _elements import Line, Node, LinePar, SagMatrix
from openglider.vector import normalize, norm


class LineSet():
    """
    Set of different lines
    Notes:
        -join some loops
        -_private functions
    """

    def __init__(self, nodes=None, lines=None, calc_par=None):
        self.calc_par = calc_par or {}  # Parameters
        self.nodes = nodes or []
        self.lines = lines or []
        self.mat = None

    def calc_geo(self, start=None):
        if start is None:
            start = self.get_lowest_lines()
        for line in start:
            if line.upper_node.type == 1:
                vec_0 = line.lower_node.vec
                t = self.get_tangential_comp(line, vec_0)
                self.nodes[line.upper_node_nr].vec = vec_0 + \
                    t * line.init_length
                conn_lines = self.get_connected_lines(line.upper_node_nr)
                self.calc_geo(conn_lines)

    def calc_sag(self, start=None):
        if start is None:
            start = self.get_lowest_lines()
        # 0 every line calculates its parameters
        self.mat = SagMatrix(len(self.lines))
        self.calc_projected_nodes()
        self.update_line_points()  # ???
        self.calc_forces(start)
        for l in self.lines:
            l.drag(self.calc_par['SPEED'])
            l.calc_length()
            l.calc_ortho_length()
            l.calc_ortho_force()
        for line in start:
            self._calc_matrix_entries(line)
        self.mat.solve_system()
        for l in self.lines:
            l.sag_par_1, l.sag_par_2 = self.mat.get_sag_par(l.number)

    def calc_stretch(self):
        pass



    # -----CALCULATE SAG-----#
    def _calc_matrix_entries(self, line):
        up = self.get_upper_conected_lines(line.upper_node_nr)
        if line.lower_node.type == 0:
            self.mat.insert_type_0_lower(line)
        else:
            lo = self.get_lower_connected_line(line.lower_node_nr)
            self.mat.insert_type_1_lower(line, lo)
        if line.upper_node.type == 1:
            self.mat.insert_type_1_upper(line, up)
        else:
            self.mat.insert_type_2_upper(line)
        for u in up:
            self._calc_matrix_entries(u)

    def calc_forces(self, start_lines):
        for line_lower in start_lines:
            vec = line_lower.get_vec()
            if line_lower.upper_node.type != 2:  # not a gallery line
                lines_upper = self.get_upper_conected_lines(
                    line_lower.upper_node.number)
                self.calc_forces(lines_upper)
                force = numpy.zeros(3)
                for line in lines_upper:
                    if line.force is None:
                        print("error line force not set")
                    else:
                        force += line.force * line.get_vec()
                #vec = line_lower.upper_node.vec - line_lower.lower_node.vec
                line_lower.force = norm(dot(force, normalize(vec)))

            else:
                force = line_lower.upper_node.force
                #vec = line_lower.upper_node.vec - line_lower.lower_node.vec
                line_lower.force = norm(proj_force(force, normalize(vec)))

    def _calc_length(self):
        """without sag..."""
        for l in self. lines:
            l.calc_length()

    def get_upper_conected_lines(self, node_nr):
        ret = []
        for l in self.lines:
            if l.lower_node_nr == node_nr:
                ret.append(l)
        return ret

    def get_lower_connected_line(self, node_nr):
        ret = []
        for l in self.lines:
            if l.upper_node_nr == node_nr:
                ret.append(l)
        if len(ret) > 1:
            print("warning!!!, there are too much lower lines")
        return ret[0]

    def calc_projected_nodes(self):
        for n in self.nodes:
            n.calc_proj_vec(self.calc_par["V_INF"])

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line, pos_vec):
        upper_node_nrs = []
        flatten(self.get_upper_influence_node(line), upper_node_nrs)
        tangent = numpy.array([0., 0., 0.])
        for node_nr in upper_node_nrs:
            tangent += self.nodes[node_nr].calc_force_infl(pos_vec)
        return normalize(tangent)

    def get_upper_influence_node(self, line):
        """get the points that have influence on the line and
        are connected to the wing"""
        upper_node = line.upper_node
        conn_l = self.get_connected_lines(upper_node.number)
        if len(conn_l) == 0:
            return upper_node.number
        else:
            return map(self.get_upper_influence_node, conn_l)

    def get_connected_lines(self, node_number):
        ret = []
        for l in self.lines:
            if l.lower_node_nr == node_number:
                ret.append(l)
        return ret

    def get_lowest_lines(self):
        ret = []
        for l in self.lines:
            n = l.lower_node
            if n.type == 0:
                ret.append(l)
        return ret

    # -----IMPORT-----#
    def update_line_points(self):
        for line in self.lines:
            line.upper_node = self.nodes[line.upper_node_nr]
            line.lower_node = self.nodes[line.lower_node_nr]

    def sort_lines(self):
        self.lines.sort(key=lambda line: line.number)
        self.nodes.sort(key=lambda node: node.number)
        # TODO: Check for consistency

    # -----VISUALISATION-----#
    def visual_output(self, sag=True, numpoints=10):
        lines = [l.get_line_coords(self.calc_par["V_INF"], sag, numpoints)
                 for l in self.lines]
        g.Graphics3D(map(g.Line, lines))


# IMPORT TEXT FILE#################
def import_lines(path):
    key_dict = {
        "NODES": [8, store_nodes, []],  # 8 tab-seperated values
        "LINES": [5, store_lines, []],
        "CALCPAR": [5, store_calc_par, {}]
    }
    return import_file(path, key_dict)


def store_nodes(values, thalist):
    n = Node(try_convert(values[0], int))
    n.type = try_convert(values[1], int)
    n.vec = numpy.array(map(lambda x: try_convert(x, float), values[2:5]))
    n.force = numpy.array(
        map(lambda x: try_convert(x, float), values[5:8]))
    thalist.append(n)


def store_lines(values, thalist):
    l = Line(try_convert(values[0], int), values[4])
    l.lower_node_nr = try_convert(values[1], int)
    l.upper_node_nr = try_convert(values[2], int)
    l.init_length = try_convert(values[3], float)
    #l.type = values[4]
    thalist.append(l)


def store_calc_par(values, calc_par):
    calc_par["GEOSTEPS"] = try_convert(values[0], int)
    calc_par["SAGSTEPS"] = try_convert(values[1], int)
    calc_par["ITER"] = try_convert(values[2], int)
    speed = calc_par["SPEED"] = try_convert(values[3], float)
    glide = calc_par["GLIDE"] = try_convert(values[4], float)
    calc_par["V_INF"] = (
        speed * normalize(numpy.array([glide, 0., 1.])))


if __name__ == "__main__":
    key_dict = import_lines("TEST_INPUT_FILE_1.txt")
    #key_dict = import_lines("TEST_INPUT_FILE_2.txt")
    #key_dict = import_lines("TEST_INPUT_FILE_3.txt")
    thalines = LineSet(
        key_dict["NODES"][2], key_dict["LINES"][2], key_dict["CALCPAR"][2])
    #print([(l.lower_node_nr, l.upper_node_nr) for l in lines.lines])
    #print([l.type for l in lines.nodes])
    thalines.update_line_points()
    strt = thalines.get_lowest_lines()
    thalines.calc_geo(strt)
    thalines.calc_sag(strt)
    thalines.visual_output(numpoints=20)
