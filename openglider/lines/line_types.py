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

import scipy.interpolate


class LineType():
    def __init__(self, name, cw, thickness, stretch_curve):
        self.name = name
        self.cw = cw
        self.thickness = thickness
        if stretch_curve[0][0] != 0:
            stretch_curve.insert(0, [0, 0])
        self.stretch_interpolation = scipy.interpolate.interp1d([p[0] for p in stretch_curve],
                                                                [p[1] for p in stretch_curve],
                                                                bounds_error=False)

    def get_stretch_factor(self, force):
        return 1 + self.stretch_interpolation(force) / 100



# SI UNITS -> thickness [m], stretch [N, %]

liros = LineType('liros', 1.1, 0.002, [[100, 1]])
liros160 = LineType('liros160', 1.1, 0.002, [[100, 1]])


cousin12100 = LineType("Cousin 12100", 1.1, 0.0006, [[50, 0.4],
                                                     [100, 0.9],
                                                     [150, 1.3],
                                                     [200, 1.5],
                                                     [250, 1.9]])


cousin16140 = LineType("Cousin 16140", 1.1, 0.0007, [[50, 0.75],
                                                     [100, 1.],
                                                     [150, 1.1],
                                                     [200, 1.4],
                                                     [250, 1.75],
                                                     [500, 2.75]])