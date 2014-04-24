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

from _functions import proj_force, proj_to_surface
from openglider.vector import normalize, norm
import numpy


class sag_matrix():
    def __init__(self, number_of_lines):
        self.size = number_of_lines * 2
        self.matrix = numpy.zeros([self.size, self.size])
        self.rhs = numpy.zeros(self.zize)

    def _type_0_lower(self, line):
        i = line.number
        self.matrix[2 * i, 2 * i + 1] = 1.

    def _type_1_lower(self, line, lower_line):
        i = line.number
        j = lower_line.number
        self.matrix[2 * i, 2 * i + 1] = 1.
        self.matrix[2 * i, 2 * j + 1] = -1
        "self.matrix[2 * i, 2 * j] = - lower_line_length"
        "self.rhs[2 * i] = q_j*l_j / Fj / 2"

    def _type_1_upper(self, line, upper_lines):
        i = line.number
        self.matrix[2 * i + 1, 2 * i] = -1
        for line_j in upper_lines:
            "j = lower_line.number"
            "self.matrix[2 * i + 1, 2 * j] = -f_jk"
        "self.rhs[2 * i + 1] =qi * li**2 /F_i /2"

    def _type_2_upper(self, line):
        "self.matrix[2 * line.number + 1, 2 * line.number] = l_i"
        self.matrix[2 * line.number + 1, 2 * line.number + 1] = 1
        "self.rhs[2 * i + 1] = -qi * li**2 /F_i /2"

    def _line_parameter(self):
        pass


class Line():

    def __init__(self, number):
        self.number = number
        self.lower_node = None
        self.upper_node = None
        self.vec = None
        self.ortho_vec = None
        self.length = None
        self.ortho_length = None
        self.force = None
        self.ortho_force = None
        self.type = None
        self.cw = None
        self.b = None
        self.sag_par_1 = None
        self.sag_par_2 = None
        self.stretch_factor = None

    def calc_stretch_par(self):
        pass

    def calc_pressure(self, speed):
        return(self.cw * self.b * speed**2/2)

    def calc_ortho_length(self, ortho_lower_vec, ortho_upper_vec):
        self.ortho_length = norm(ortho_lower_vec - ortho_upper_vec)


class Node():

    def __init__(self, number):
        self.number = number
        self.type = None
        self.vec = numpy.array([None, None, None])
        self.vec_proj = numpy.array([None, None, None])
        self.force = numpy.array([None, None, None])
        self.length = None

    def calc_force_infl(self, vec):
        v = numpy.array(vec)
        if None in self.force:
            print("force in node " + str(self.number) + " not set")
        elif None in self.vec:
            print("vec in node " + str(self.number) + " not set")
        elif self.type != 2:
            print("wrong node type, node " + str(self.number))
        else:
            return(proj_force(self.force, self.vec - v) *
                   normalize(self.vec - v))

    def calc_proj_vec(self, v_inf):
        if None in self.vec:
            print("node " + str(self.number) + "not set yet")
        else:
            self.vec_proj = proj_to_surface(self.vec, v_inf)


class LinePar():
    def __init__(self, name):
        self.type = name
        self.cw = 0.
        self.b = 0.
        self.strech_factor = 0.
