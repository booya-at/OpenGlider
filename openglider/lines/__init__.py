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
import copy
import numpy
from numpy import dot
from openglider.lines.elements import Line, Node, SagMatrix
from openglider.lines.functions import proj_force, flatten
from openglider.vector import norm, normalize


class LineSet():
    """
    Set of different lines
    """
    def __init__(self, lines=None, calc_par=None):
        self.calc_par = calc_par or {}  # Parameters
        self.lines = lines or []
        self.mat = None

    @property
    def lowest_lines(self):
        res = set()
        for l in self.lines:
            n = l.lower_node
            #print(n.type)
            if n.type == 0:
                res.add(l)
                # maybe only return
        return res

    @property
    def nodes(self):
        nodes = set()
        for line in self.lowest_lines:
            nodes.add(line.lower_node)
        for line in self.lines:
            nodes.add(line.upper_node)
        return nodes

    def calc_geo(self, start=None):
        if start is None:
            start = self.lowest_lines
        for line in start:
            #print(line.number)
            if line.upper_node.type == 1:
                vec_0 = line.lower_node.vec
                t = self.get_tangential_comp(line, vec_0)
                line.upper_node.vec = vec_0 + t * line.init_length
                #print(line.upper_node.vec)
                conn_lines = self.get_upper_conected_lines(line.upper_node)
                self.calc_geo(conn_lines)

    def calc_sag(self, start=None):
        if start is None:
            start = self.lowest_lines
        # 0 every line calculates its parameters
        self.mat = SagMatrix(len(self.lines))
        self.calc_projected_nodes()
        self.calc_forces(start)
        for line in start:
            self._calc_matrix_entries(line)
        #print(self.mat)
        self.mat.solve_system()
        for l in self.lines:
            l.sag_par_1, l.sag_par_2 = self.mat.get_sag_par(l.number)

    def calc_stretch(self):
        pass  # could be done in the line itself

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self):
        mirror_vector = numpy.array([1, -1, 1])
        for node in self.nodes:
            if node.type != 1:
                node.vec = mirror_vector*node.vec

    # -----CALCULATE SAG-----#
    def _calc_matrix_entries(self, line):
        upper_lines = self.get_upper_conected_lines(line.upper_node)
        if line.lower_node.type == 0:
            self.mat.insert_type_0_lower(line)
        else:
            lo = self.get_lower_connected_line(line.lower_node)
            self.mat.insert_type_1_lower(line, lo)
        if line.upper_node.type == 1:
            self.mat.insert_type_1_upper(line, upper_lines)
        else:
            self.mat.insert_type_2_upper(line)
        for line in upper_lines:
            self._calc_matrix_entries(line)

    def calc_forces(self, start_lines):
        for line_lower in start_lines:
            vec = line_lower.diff_vector
            if line_lower.upper_node.type != 2:  # not a gallery line
                lines_upper = self.get_upper_conected_lines(
                    line_lower.upper_node)
                self.calc_forces(lines_upper)
                force = numpy.zeros(3)
                for line in lines_upper:
                    if line.force is None:
                        print("error line force not set")
                    else:
                        force += line.force * line.diff_vector

                line_lower.force = dot(force, normalize(vec))

            else:
                force = line_lower.upper_node.force
                line_lower.force = 1/proj_force(force, normalize(vec))

    def get_upper_conected_lines(self, node):
        lines = []
        for line in self.lines:
            if line.lower_node is node:
                lines.append(line)
        return lines

    def get_lower_connected_line(self, node):
        lines = []
        for line in self.lines:
            if line.upper_node is node:
                lines.append(line)
        #if len(ret) > 1:
        #    print("warning!!!, there are too much lower lines")
        return lines[0]

    def get_connected_lines(self, node):
        lines = []
        for l in self.lines:
            if l.lower_node is node:
                lines.append(l)
        return lines

    def calc_projected_nodes(self):
        for n in self.nodes:
            n.calc_proj_vec(self.calc_par["V_INF"])

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line, pos_vec):
        top_nodes = self.get_top_influence_nodes(line)
        tangent = numpy.array([0., 0., 0.])
        for node in top_nodes:
            tangent += node.calc_force_infl(pos_vec)
        return normalize(tangent)  # TODO: why normalize?

    def get_top_influence_nodes(self, line):
        """get the points that have influence on the line and
        are connected to the wing"""
        upper_node = line.upper_node
        if upper_node.type == 2:
            return upper_node
        else:
            nodes = []
            for line in self.get_upper_conected_lines(upper_node):
                nodes.append(self.get_top_influence_nodes(line))
            return nodes

    # -----IMPORT-----#
    def sort_lines(self):
        self.lines.sort(key=lambda line: line.number)
        #self.nodes.sort(key=lambda node: node.number)
        # TODO: Check for consistency

    # -----VISUALISATION-----#
    # def visual_output(self, sag=True, numpoints=10):
    #     lines = [l.get_line_coords(self.calc_par["V_INF"], sag, numpoints)
    #              for l in self.lines]
    #     g.Graphics3D(map(g.Line, lines))


