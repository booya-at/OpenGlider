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
import os
import random
import sys
import numpy
import math

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
import openglider.Graphics
import openglider.plots
from openglider.Vector import norm, Vectorlist2D

testfolder = os.path.dirname(os.path.abspath(__file__))


def test_glider(path=testfolder + '/demokite.ods'):
    glider = openglider.Glider()
    glider.import_geometry(path)
    glider.close_rib(-1)  # Stabi
    glider.recalc()
    # TODO: Miniribs for mirrored cells fail
    startpoint = startpoint2 = 0
    marks = []
    cuts = []

    for cell in glider.cells:
        left, right = openglider.plots.flattened_cell(cell)

        left_out = left.copy()
        right_out = right.copy()
        left_out.add_stuff(-0.02)
        right_out.add_stuff(0.02)

        diff = left[len(left)]-left[0]
        angle = math.asin(diff[0]/norm(diff))
        #print(angle*180/math.pi)
        #angle = 0
        for part in [left, right, left_out, right_out]:
            part.rotate(-angle)
            part.check()

        cuts_front = [random.random()*len(left)*0.1 for __ in range(2)]
        cuts_back = [(random.random()+1)*len(left)*0.2 for __ in range(2)]

        outlist_1, leftcut, rightcut = openglider.plots.cut_1([[left, cuts_front[0]], [right, cuts_front[1]]],
                                                              left_out, right_out, -0.02)
        outlist_2, leftcut_2, rightcut_2 = openglider.plots.cut_2([[left, cuts_back[0]], [right, cuts_back[1]]],
                                                                  left_out, right_out, 0.02)
        left = (left[cuts_front[0]:cuts_back[0]])
        right = (right[cuts_front[1]:cuts_back[1]])
        left_out = (left_out[leftcut:leftcut_2])
        right_out = (right_out[rightcut:rightcut_2])


        diff = 0
        for p in right:
            if p[0] - startpoint > diff:
                startpoint2 = p[0]
                diff = startpoint2 - startpoint
        marks.append(left + numpy.array([startpoint, 0]))
        marks.append(right + numpy.array([startpoint, 0]))
        cuts.append(left_out + numpy.array([startpoint, 0]))
        cuts.append(outlist_1 + numpy.array([startpoint, 0]))
        cuts.append(right_out + numpy.array([startpoint, 0]))
        cuts.append(outlist_2 + numpy.array([startpoint, 0]))
        startpoint += startpoint2 + 0.4

    #print(cuts[0].data)

    openglider.Graphics.Graphics([openglider.Graphics.Line(cut) for cut in cuts[:]] +
                                 [openglider.Graphics.Point(mark) for mark in marks[:]])








test_glider()
