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
from openglider.vector import normalize
import numpy


class Line():

    def __init__(self, number):
        self.number = number
        self.lower_node = None
        self.upper_node = None
        self.length = None
        self.type = None
        self.cw = None
        self.b = None
        self.strech_factor = None
        self.sag_par_1 = None
        self.sag_par_2 = None
        self.stretch_factor = None

    def calc_matrix_cooef(self):
        pass
 
    def calc_stretch_par(self):
        pass

    def calc_length(self):
        pass


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
