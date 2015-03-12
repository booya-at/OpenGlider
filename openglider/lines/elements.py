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

import numpy

from openglider.lines import line_types
from openglider.lines.functions import proj_force, proj_to_surface
from openglider.utils.cache import cached_property, CachedObject
from openglider.vector import PolyLine
from openglider.vector.functions import norm, normalize


class SagMatrix():
    def __init__(self, number_of_lines):
        size = number_of_lines * 2
        self.matrix = numpy.zeros([size, size])
        self.rhs = numpy.zeros(size)
        self.solution = numpy.zeros(size)

    def __str__(self):
        return str(self.matrix) + "\n" + str(self.rhs)

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
        self.rhs[2 * i + 1] = -lower_line.ortho_pressure * \
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
            infl = u.force_projected * numpy.dot(vec, u.diff_vector_projected)
            infl_list.append(infl)
        sum_infl = sum(infl_list)
        for k in range(len(upper_lines)):
            j = upper_lines[k].number
            self.matrix[2 * i, 2 * j] = -(infl_list[k] / sum_infl)
        self.rhs[2 * i] = line.ortho_pressure * \
            line.length_projected / line.force_projected

    def insert_type_2_upper(self, line):
        """
        Fixed upper node
        """
        i = line.number
        self.matrix[2 * line.number, 2 * line.number] = line.length_projected
        self.matrix[2 * line.number, 2 * line.number + 1] = 1.
        self.rhs[2 * i] = line.ortho_pressure * \
            line.length_projected ** 2 / line.force_projected / 2

    def solve_system(self):
        self.solution = numpy.linalg.solve(self.matrix, self.rhs)

    def get_sag_parameters(self, line_nr):
        return [
            self.solution[line_nr * 2],
            self.solution[line_nr * 2 + 1]]


class Line(CachedObject):
    def __init__(self, lower_node, upper_node, vinf,
                 line_type=line_types.liros.liros, target_length=None, number=None):
        """
        Line Class
        """
        self.number = number
        self.type = line_type  # type of line

        self.v_inf = vinf

        self.lower_node = lower_node
        self.upper_node = upper_node

        self.target_length = target_length
        self.init_length = target_length

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

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf')
    def length_projected(self):
        return norm(self.lower_node.vec_proj - self.upper_node.vec_proj)

    @property
    def length_no_sag(self):
        return norm(self.upper_node.vec - self.lower_node.vec)

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf', 'sag_par_1', 'sag_par_2')
    def length_with_sag(self):
        if self.sag_par_1 is None or self.sag_par_2 is None:
            raise ValueError('Sag not yet calculated!')

        return PolyLine(self.get_line_points(numpoints=100)).get_length()

    def get_stretched_length(self, pre_load=50):
        """
        Get the total line-length for production using a given stretch
        length = len_0 * (1 + stretch*force)
        """
        factor = self.type.get_stretch_factor(pre_load) / self.type.get_stretch_factor(self.force)
        return self.length_with_sag * factor

    #@cached_property('v_inf', 'type.cw', 'type.thickness')
    @property
    def ortho_pressure(self):
        """drag per meter (projected)"""
        return 1 / 2 * self.type.cw * self.type.thickness * norm(self.v_inf) ** 2

    @cached_property('lower_node.vec', 'upper_node.vec', 'v_inf')
    def drag_total(self):
        return self.ortho_pressure * self.length_projected

    @cached_property('force', 'lower_node.vec', 'upper_node.vec')
    def force_projected(self):
        return self.force * self.length_projected / self.length_no_sag

    def get_line_points(self, sag=True, numpoints=10):
        """
        Return points of the line
        """
        if self.sag_par_1 is None or self.sag_par_2 is None:
            sag=False
        return [self.get_line_point(i / (numpoints - 1), sag=sag) for i in range(numpoints)]

    def get_line_point(self, x, sag=True):
        """pos(x) [x,y,z], x: [0,1]"""
        if sag:
            return (self.lower_node.vec * (1. - x) + self.upper_node.vec * x +
                    self.get_sag(x) * self.v_inf_0)
        else:
            return self.lower_node.vec * (1. - x) + self.upper_node.vec * x

    def get_sag(self, x):
        """sag u(x) [m], x: [0,1]"""
        xi = x * self.length_projected
        u = (- xi ** 2 / 2 * self.ortho_pressure /
             self.force_projected + xi *
             self.sag_par_1 + self.sag_par_2)
        return u

    @property
    def _get_projected_par(self):
        c1_n = numpy.dot(self.lower_node.get_diff(), self.v_inf_0)
        c2_n = numpy.dot(self.upper_node.get_diff(), self.v_inf_0)
        return [c1_n + self.sag_par_1, c2_n / self.length_projected + self.sag_par_2]

    def __json__(self):
        if isinstance(self.v_inf, numpy.ndarray):
            v_inf = self.v_inf.tolist()
        else:
            v_inf = list(self.v_inf)
        return{
            'number': self.number,
            'lower_node': self.lower_node,
            'upper_node': self.upper_node,
            'vinf': v_inf,
            'line_type': self.type.name,
            'target_length': self.target_length
        }

    @classmethod
    def __from_json__(cls, number, lower_node, upper_node, vinf, line_type, target_length):
        return cls(lower_node,
                   upper_node,
                   vinf,
                   # TODO: Find elegant solution
                   getattr(line_types, line_type),
                   target_length,
                   number)


class Node(object):
    def __init__(self, node_type, position_vector=None):
        self.type = node_type  # lower, top, middle (0, 2, 1)
        self.vec = position_vector

        self.vec_proj = None  # pos_proj
        self.force = numpy.array([None, None, None])  # top-node force

    def calc_force_infl(self, vec):
        v = numpy.array(vec)
        return normalize(self.vec - v) * proj_force(self.force, self.vec - v)

    def calc_proj_vec(self, v_inf):
        self.vec_proj = proj_to_surface(self.vec, v_inf)
        return proj_to_surface(self.vec, v_inf)

    def get_diff(self):
        return self.vec - self.vec_proj

    def __json__(self):
        return{
            'node_type': self.type,
            'position_vector': list(self.vec)
        }
