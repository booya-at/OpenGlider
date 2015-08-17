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
from __future__ import division

import copy
import numpy
from numpy import dot

from openglider.lines.elements import Line, Node, SagMatrix
from openglider.lines.functions import proj_force
from openglider.lines.line_types import LineType
from openglider.vector.functions import norm, normalize

__all__ = ["Line", "Node", "LineSet"]


class LineSet():
    """
    Set of different lines
    TODO:
        -add stretch
    """

    def __init__(self, lines=None, v_inf=None):
        self.v_inf = numpy.array(v_inf) if v_inf is not None else numpy.array([0, 0, 0])  # Parameters
        self.lines = lines or []
        self.mat = None

    @property
    def lowest_lines(self):
        return [line for line in self.lines if line.lower_node.type == 0]

    @property
    def nodes(self):
        nodes = set()
        for line in self.lines:
            nodes.add(line.upper_node)
            nodes.add(line.lower_node)
        return nodes

    @property
    def total_length(self):
        length = 0
        for line in self.lines:
            length += line.get_stretched_length()
        return length

    def calc_geo(self, start=None):
        if start is None:
            start = self.lowest_lines
        for line in start:
            # print(line.number)
            if line.upper_node.type == 1:  # no gallery line
                lower_point = line.lower_node.vec
                tangential = self.get_tangential_comp(line, lower_point)
                line.upper_node.vec = lower_point + tangential * line.init_length

                self.calc_geo(self.get_upper_connected_lines(line.upper_node))

    def calc_sag(self, start=None):
        if start is None:
            start = self.lowest_lines
        # 0 every line calculates its parameters
        self.mat = SagMatrix(len(self.lines))
        self.calc_projected_nodes()
        self.calc_forces(start)
        for line in start:
            self.calc_matrix_entries(line)
        # print(self.mat)
        self.mat.solve_system()
        for l in self.lines:
            l.sag_par_1, l.sag_par_2 = self.mat.get_sag_parameters(l.number)

    # -----CALCULATE SAG-----#
    def calc_matrix_entries(self, line):
        up = self.get_upper_connected_lines(line.upper_node)
        if line.lower_node.type == 0:
            self.mat.insert_type_0_lower(line)
        else:
            lo = self.get_lower_connected_lines(line.lower_node)
            self.mat.insert_type_1_lower(line, lo[0])

        if line.upper_node.type == 1:
            self.mat.insert_type_1_upper(line, up)
        else:
            self.mat.insert_type_2_upper(line)
        for u in up:
            self.calc_matrix_entries(u)

    def calc_forces(self, start_lines):
        for line_lower in start_lines:
            vec = line_lower.diff_vector
            if line_lower.upper_node.type != 2:  # not a gallery line
                lines_upper = self.get_upper_connected_lines(
                    line_lower.upper_node)
                self.calc_forces(lines_upper)
                force = numpy.zeros(3)
                for line in lines_upper:
                    if line.force is None:
                        print("error line force not set")
                    else:
                        force += line.force * line.diff_vector
                # vec = line_lower.upper_node.vec - line_lower.lower_node.vec
                line_lower.force = norm(dot(force, normalize(vec)))

            else:
                force = line_lower.upper_node.force
                line_lower.force = norm(proj_force(force, normalize(vec)))

    def get_upper_connected_lines(self, node):
        return [line for line in self.lines if line.lower_node is node]

    def get_lower_connected_lines(self, node):
        return [line for line in self.lines if line.upper_node is node]

    def get_connected_lines(self, node):
        return self.get_upper_connected_lines(node) + self.get_lower_connected_lines(node)

    def calc_projected_nodes(self):
        for n in self.nodes:
            n.calc_proj_vec(self.v_inf)

    # -----CALCULATE GEO-----#
    def get_tangential_comp(self, line, pos_vec):
        upper_node_nrs = self.get_upper_influence_node(line)
        tangent = numpy.array([0., 0., 0.])
        for node in upper_node_nrs:
            tangent += node.calc_force_infl(pos_vec)
        return normalize(tangent)

    def get_upper_influence_node(self, line):
        """get the points that have influence on the line and
        are connected to the wing"""
        upper_node = line.upper_node
        if upper_node.type == 2:
            return [upper_node]
        else:
            upper_lines = self.get_upper_connected_lines(upper_node)
            result = []
            for upper_line in upper_lines:
                result += self.get_upper_influence_node(upper_line)
            return result

    def iterate_target_length(self, steps=10, fac=0.5, pre_load=50):
        '''iterative methode to satisfy the target length'''
        for i in range(steps):
            for l in self.lines:
                if l.target_length is not None:
                    l.init_length = l.target_length * l.init_length / l.get_stretched_length(pre_load)
            print("------")
            self.calc_geo()
            self.calc_sag()

    def sort_lines(self):
        self.lines.sort(key=lambda line: line.number)
        # self.nodes.sort(key=lambda node: node.number)
        # TODO: Check for consistency

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def from_2d(cls, lines, points):
        pass

    def __json__(self):
        new = self.copy()
        nodes = list(new.nodes)
        for line in new.lines:
            line.upper_node = nodes.index(line.upper_node)
            line.lower_node = nodes.index(line.lower_node)

        return {
            'lines': new.lines,
            'nodes': nodes,
            'v_inf': self.v_inf.tolist()
        }

    @classmethod
    def __from_json__(cls, lines, nodes, v_inf):
        for line in lines:
            if isinstance(line.upper_node, int):
                line.upper_node = nodes[line.upper_node]
            if isinstance(line.lower_node, int):
                line.lower_node = nodes[line.lower_node]
        return cls(lines, v_inf)
