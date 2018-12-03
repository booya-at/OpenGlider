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
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/
from __future__ import division
import sys

from openglider.vector import Interpolation


class LineType():
    types = {}

    def __init__(self, name, thickness, stretch_curve, min_break_load=None, weight=None, cw=1.1):
        """
        Line Type
        Attributes:
            - name
            - cw (usually 1.1)
            - thickness (in mm)
            - stretch curve: [[force [N], stretch_in_%],...]
            - resistance: minimal break strength
            - weight in g/m
        """
        self.name = name
        self.types[name] = self
        self.cw = cw
        self.thickness = thickness / 1000
        if stretch_curve[0][0] != 0:
            stretch_curve.insert(0, [0, 0])
        self.stretch_curve = stretch_curve
        self.stretch_interpolation = Interpolation(stretch_curve, extrapolate=True)
        self.weight = weight

        self.min_break_load = min_break_load

    def get_stretch_factor(self, force):
        return 1 + self.stretch_interpolation(force) / 100

    @classmethod
    def get(cls, name):
        try:
            return cls.types[name]
        except KeyError:
            raise KeyError("Line-type {} not found".format(name))



# SI UNITS -> thickness [mm], stretch [N, %]

