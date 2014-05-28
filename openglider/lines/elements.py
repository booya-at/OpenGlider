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
from functions import proj_force, proj_to_surface
from openglider.utils.cached_property import cached_property
from openglider.vector import normalize, norm
from openglider.lines import line_types
import numpy


class SagMatrix():

    def __init__(self, number_of_lines):
        size = number_of_lines * 2
        self.matrix = numpy.zeros([size, size])
        self.rhs = numpy.zeros(size)
        self.solution = numpy.zeros(size)

    def __str__(self):
        return(str(self.matrix) + "\n" + str(self.rhs))

    def insert_type_0_lower(self, line):
        """
        fixed lower node
        """
        i = line.number
        self.matrix[2 * i + 1, 2 * i + 1] = 1.

    def insert_type_1_lower(self, line, lower_line):
        """
        free lower node
        """
        i = line.number
        j = lower_line.number
        self.matrix[2 * i + 1, 2 * i + 1] = 1.
        self.matrix[2 * i + 1, 2 * j + 1] = -1.
        self.matrix[2 * i + 1, 2 * j] = -lower_line.length_projected
        self.rhs[2 * i + 1] = -lower_line.drag_differential * \
            lower_line.length_projected ** 2 / lower_line.force_projected / 2

    def insert_type_1_upper(self, line, upper_lines):
        """
        free upper node
        """
        i = line.number
        self.matrix[2 * i, 2 * i] = 1
        infl_list = []
        vec = line.diff_vector_projected
        for u in upper_lines:
            infl = line.force_projected * \
                numpy.dot(vec, u.diff_vector_projected)
            infl_list.append(infl)
        sum_infl = sum(infl_list)
        for k in range(len(upper_lines)):
            j = upper_lines[k].number
            self.matrix[2 * i, 2 * j] = -(infl_list[k] / sum_infl)
        self.rhs[2 * i] = line.drag_differential * \
            line.length_projected / line.force_projected

    def insert_type_2_upper(self, line):
        """
        Fixed upper node
        """
        i = line.number
        self.matrix[2 * line.number, 2 * line.number] = line.length_projected
        self.matrix[2 * line.number, 2 * line.number + 1] = 1.
        self.rhs[2 * i] = line.drag_differential * \
            line.length_projected ** 2 / line.force_projected / 2

    def solve_system(self):
        self.solution = numpy.linalg.solve(self.matrix, self.rhs)

    def get_sag_par(self, line_nr):
        return [
            self.solution[line_nr * 2],
            self.solution[line_nr * 2 + 1]]

    def _line_parameter(self):
        pass


class Line(object):
    # TODO: why not directly save the line_type instead of a string
    # TODO: why are lower_node and upper_node not mandatory?
    # TODO: cached properties?

    def __init__(self, number, lower_node, upper_node,
                 vinf=None, line_type=line_types.liros, init_length=None):
        """Line Class:
        Note:
            -for easier use the lines have it's nodes directly as variables!!!
            -when you set some parameter of a node always use the node
                dict and don't forget to update the lines.
            -when you get parameters of nodes, you can the take them from
                the node dict or from the nodes stored in the line.
            """
        self.number = number
        self.type = line_type                # type of line

        self.v_inf = numpy.array([10, 0, 1]) if vinf is None else vinf
        self.lower_node = lower_node
        self.upper_node = upper_node

        self.init_length = init_length

        self.force = None

        self.sag_par_1 = None
        self.sag_par_2 = None

    @property
    def v_inf_0(self):
        return normalize(self.v_inf)

    #@cached_property('lower_node.vec', 'upper_node.vec')
    @property
    def diff_vector(self):
        return normalize(self.upper_node.vec - self.lower_node.vec)

    #@cached_property('lower_node.vec', 'upper_node.vec')
    @property
    def diff_vector_projected(self):
        return normalize(self.upper_node.vec_proj - self.lower_node.vec_proj)

    #@cached_property('lower_node.vec', 'upper_node.vec')
    @property
    def length_no_sag(self):
        return norm(self.upper_node.vec - self.lower_node.vec)

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf', 'sag_par_1', 'sag_par_2')
    def length_with_sag(self):
        if self.sag_par_1 and self.sag_par_2:
            return 0
        else:
            print('Sag not yet calculated!')
            return self.length_no_sag

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf')
    #@property
    def length_projected(self):
        return norm(self.lower_node.vec_proj - self.upper_node.vec_proj)
        # return self.ortho_length

    #@cached_property('v_inf', 'type.cw', 'type.thickness')
    @property
    def drag_differential(self):
        """drag per meter"""
        return 1 / 2 * self.type.cw * self.type.thickness * norm(self.v_inf) ** 2

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf')
    def drag_total(self):
        return self.drag_differential * self.length_projected

    @cached_property('force', 'lower_node.vec', 'upper_node.vec')
    def force_projected(self):
        return self.force * self.length_projected / self.length_no_sag

    def get_line_points(self, sag=True, numpoints=10):
        """
        Return points of the line
        """
        points = []
        for i in range(numpoints):
            points.append(self.get_line_point(i / (numpoints - 1), sag=sag))
        return points

    def get_line_point(self, x, sag=True):
        """pos(x) [x,y,z], x: [0,1]"""
        return self.lower_node.vec * (1. - x) + self.upper_node.vec * x + self.get_sag(x) * self.v_inf_0

    def get_sag(self, x):
        """sag u(x) [m], x: [0,1]"""
        xi = x * self.length_projected
        u = (- xi ** 2 / 2 * self.drag_differential /
             self.force_projected + xi *
             self.sag_par_1 + self.sag_par_2)
        #print(self.length_projected, u)
        return u

    def calc_stretch_par(self):
        pass


class Node(object):

    def __init__(self, node_type, pos=None):
        self.type = node_type  # lower, top, middle (0, 2, 1)
        self.vec = pos

        self.vec_proj = None  # pos_proj
        self.force = numpy.array([None, None, None])  # top-node force

    def calc_force_infl(self, vec):
        v = numpy.array(vec)
        return normalize(self.vec - v) / proj_force(self.force, self.vec - v)

    def calc_proj_vec(self, v_inf):
        self.vec_proj = proj_to_surface(self.vec, v_inf)
        return proj_to_surface(self.vec, v_inf)


class LinePar():

    def __init__(self, name):
        self.type = name
        self.cw = 0.
        self.b = 0.
        self.strech_factor = 0.
