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

import math
import sys
import os

from openglider.plots import flattened_cell, cuts


try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
import openglider.graphics
import openglider.airfoil
from openglider.glider.ballooning import BallooningBezier
from openglider.plots.projection import flatten_list
import openglider.plots
from openglider.glider.cell import Cell
from openglider.glider.rib import Rib
import numpy


prof = openglider.airfoil.Profile2D.import_from_dat(os.path.dirname(os.path.abspath(__file__)) + "/testprofile.dat")

ballooning = BallooningBezier()
balloon = [ballooning(i) for i in prof.x_values]

r1 = Rib(prof, ballooning, [0., 0.12, 0], 1., 20 * math.pi / 180, 2 * math.pi / 180, 0, 7.)
r2 = r1.copy()
r2.mirror()

left, right = flatten_list(r2.profile_3d.data, r1.profile_3d.data)
ding = [numpy.array([0, 0]), numpy.array([1., 0])]

#[numpy.array([0,0]),numpy.array([1,0])

cell = Cell(r1, r2)
left_bal, left2, right2, right_bal = flattened_cell(cell)
left_out = left2.copy()
left_out.add_stuff(-0.02)
right_out = right2.copy()
right_out.add_stuff(0.02)


openglider.graphics.Graphics2D([openglider.graphics.Line(left.data), openglider.graphics.Line(right.data),
                                openglider.graphics.Line(left2.data), openglider.graphics.Line(right2.data),
                                openglider.graphics.Line(left_out.data),
                                openglider.graphics.Line(right_out.data)])


################CUTS
outlist, leftcut, rightcut = cuts[1]([[left2, 0], [right2, 0]], left_out, right_out, -0.02)
end = 150
outlist2, leftcut2, rightcut2 = cuts[0]([[left2, end], [right2, end]], left_out, right_out, 0.02)

openglider.graphics.Graphics2D([openglider.graphics.Line(left2.data[0:end]),
                                openglider.graphics.Line(right2.data[0:end]),
                                openglider.graphics.Line(left_out[leftcut:leftcut2]),
                                openglider.graphics.Line(outlist),
                                openglider.graphics.Line(right_out[rightcut:rightcut2]),
                                openglider.graphics.Line(outlist2)])



#right.rotate(2., right[0])
#openglider.graphics.Graphics2D([openglider.graphics.Line(left.data), openglider.graphics.Line(right.data)])