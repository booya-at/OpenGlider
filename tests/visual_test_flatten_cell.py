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
try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
import openglider.Cells
import openglider.Graphics
import openglider.Ribs
import openglider.Profile
from openglider.Utils.Ballooning import BallooningBezier
from openglider.Vector.projection import flatten_list
import openglider.plots
import numpy
__author__ = 'simon'


prof = openglider.Profile.Profile2D()
prof.importdat(os.path.dirname(os.path.abspath(__file__)) + "/testprofile.dat")

ballooning = BallooningBezier()
balloon = [ballooning(i) for i in prof.x_values]

r1 = openglider.Ribs.Rib(prof, ballooning, [0., 0.12, 0], 1., 20 * math.pi / 180, 2 * math.pi / 180, 0, 7.)
r2 = r1.copy()
r2.mirror()
r1.recalc()
r2.recalc()

left, right = flatten_list(r2.profile_3d.data, r1.profile_3d.data)
ding = [numpy.array([0, 0]), numpy.array([1., 0])]

#[numpy.array([0,0]),numpy.array([1,0])

cell = openglider.Cells.Cell(r1, r2)
left2, right2 = openglider.plots.flattened_cell(cell)
left_out = left2.copy()
left_out.add_stuff(-0.02)
right_out = right2.copy()
right_out.add_stuff(0.02)


openglider.Graphics.Graphics2D([openglider.Graphics.Line(left.data), openglider.Graphics.Line(right.data),
                                openglider.Graphics.Line(left2.data), openglider.Graphics.Line(right2.data),
                                openglider.Graphics.Line(left_out.data),
                                openglider.Graphics.Line(right_out.data)])


################CUTS
outlist, leftcut, rightcut = openglider.plots.cut_2([[left2,0], [right2,0]], left_out, right_out, -0.02)
end = 150
outlist2, leftcut2, rightcut2 = openglider.plots.cut_1([[left2, end], [right2, end]], left_out, right_out, 0.02)

openglider.Graphics.Graphics2D([openglider.Graphics.Line(left2.data[0:end]),
                                openglider.Graphics.Line(right2.data[0:end]),
                                openglider.Graphics.Line(left_out[leftcut:leftcut2]),
                                openglider.Graphics.Line(outlist),
                                openglider.Graphics.Line(right_out[rightcut:rightcut2]),
                                openglider.Graphics.Line(outlist2)])



#right.rotate(2., right[0])
#openglider.Graphics.Graphics2D([openglider.Graphics.Line(left.data), openglider.Graphics.Line(right.data)])