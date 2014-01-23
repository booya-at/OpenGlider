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
import unittest
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
importpath = testfolder+"/demokite.ods"

class Test_Glider_Flatten(unittest.TestCase):
    def setUp(self):
        self.glider = openglider.Glider()
        self.glider.import_geometry(path=importpath)
        self.glider.recalc()

    def get_flattened(self):
        cell = self.glider.cells[random.randint(0, len(self.glider.cells)-1)]
        left, right = openglider.plots.flattened_cell(cell)
        left_out = left.copy()
        right_out = right.copy()
        left_out.add_stuff(-0.02)
        right_out.add_stuff(0.02)
        return left_out, left, right, right_out


    def test_cut1(self):
        left_out, left, right, right_out = self.get_flattened()
        cuts_front = [random.random()*len(left)*0.1 for __ in range(2)]
        cuts_back = [(random.random()+1)*len(left)*0.2 for __ in range(2)]
        outlist_1, leftcut, rightcut = openglider.plots.cut_1([[left, cuts_front[0]], [right, cuts_front[1]]],
                                                              left_out, right_out, -0.02)
        outlist_2, leftcut_2, rightcut_2 = openglider.plots.cut_1([[left, cuts_back[0]], [right, cuts_back[1]]],
                                                                  left_out, right_out, 0.02)
        cuts = [left_out[leftcut:leftcut_2], outlist_1, right_out[rightcut:rightcut_2], outlist_2]
        marks = [left[cuts_front[0]:cuts_back[0]], right[cuts_front[1]:cuts_back[1]]]
        openglider.Graphics.Graphics2D([openglider.Graphics.Line(list) for list in cuts] +
                                       [openglider.Graphics.Point(list) for list in marks])

    def test_cut2(self):
        left_out, left, right, right_out = self.get_flattened()
        cuts_front = [random.random()*len(left)*0.1 for __ in range(2)]
        cuts_back = [(random.random()+1)*len(left)*0.2 for __ in range(2)]
        outlist_1, leftcut, rightcut = openglider.plots.cut_2([[left, cuts_front[0]], [right, cuts_front[1]]],
                                                              left_out, right_out, -0.02)
        outlist_2, leftcut_2, rightcut_2 = openglider.plots.cut_2([[left, cuts_back[0]], [right, cuts_back[1]]],
                                                                  left_out, right_out, 0.02)
        cuts = [left_out[leftcut:leftcut_2], outlist_1, right_out[rightcut:rightcut_2], outlist_2]
        marks = [left[cuts_front[0]:cuts_back[0]], right[cuts_front[1]:cuts_back[1]]]
        openglider.Graphics.Graphics2D([openglider.Graphics.Line(list) for list in cuts] +
                                       [openglider.Graphics.Point(list) for list in marks])

    def test_cut3(self):
        left_out, left, right, right_out = self.get_flattened()
        cuts_front = [random.random()*len(left)*0.1 for __ in range(2)]
        cuts_back = [(random.random()+1)*len(left)*0.2 for __ in range(2)]
        outlist_1, leftcut, rightcut = openglider.plots.cut_3([[left, cuts_front[0]], [right, cuts_front[1]]],
                                                              left_out, right_out, -0.02)
        outlist_2, leftcut_2, rightcut_2 = openglider.plots.cut_3([[left, cuts_back[0]], [right, cuts_back[1]]],
                                                                  left_out, right_out, 0.02)
        cuts = [left_out[leftcut:leftcut_2], outlist_1, right_out[rightcut:rightcut_2], outlist_2]
        marks = [left[cuts_front[0]:cuts_back[0]], right[cuts_front[1]:cuts_back[1]]]
        openglider.Graphics.Graphics2D([openglider.Graphics.Line(list) for list in cuts] +
                                       [openglider.Graphics.Point(list) for list in marks])


