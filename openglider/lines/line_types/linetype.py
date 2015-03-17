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

import scipy.interpolate


class LineType():
    types = {}

    def __init__(self, name, cw, thickness, stretch_curve, resistance=None):
        """
        Line Type
        Attributes:
            - name
            - cw (usually 1.1)
            - thickness (in m)
            - stretch curve: [[force, stretch_in_%],...]
            - resistance: minimal break strength
        """
        self.name = name
        self.types[name] = self
        self.cw = cw
        self.thickness = thickness
        if stretch_curve[0][0] != 0:
            stretch_curve.insert(0, [0, 0])
        self.stretch_curve = stretch_curve
        self.stretch_interpolation = scipy.interpolate.interp1d([p[0] for p in stretch_curve],
                                                                [p[1] for p in stretch_curve],
                                                                bounds_error=False)

        self.resistance = resistance

    def get_stretch_factor(self, force):
        return 1 + self.stretch_interpolation(force) / 100

    @classmethod
    def get(cls, name):
        try:
            return cls.types[name]
        except KeyError:
            raise KeyError("Line-type {} not found".format(name))



# SI UNITS -> thickness [m], stretch [N, %]

