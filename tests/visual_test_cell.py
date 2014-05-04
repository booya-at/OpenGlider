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


#!/bin/python2
import random
import unittest
import os
import math
import sys

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.airfoil import Profile2D
from openglider.glider.cell import Cell
from openglider.glider.rib import Rib
import openglider.graphics as Graph
from openglider.glider.ballooning import BallooningBezier


class TestCell(unittest.TestCase):
    def setUp(self, numpoints=100):
        self.prof1 = Profile2D()
        self.prof2 = Profile2D()
        for prof in [self.prof1, self.prof2]:
            naca = random.randint(1, 1399)
            prof.compute_naca(naca=1223, numpoints=numpoints)
            prof.close()
            prof.normalize()
        self.ballooning = BallooningBezier()
        self.rib2 = Rib(self.prof1, self.ballooning, [0., 0.12, 0], 1., 20 * math.pi / 180, 2 * math.pi / 180, 0, 7.)
        self.rib3 = Rib(self.prof2, self.ballooning, [0.2, 0.3, -0.1], 0.8, 30 * math.pi / 180, 5 * math.pi / 180, 0, 7.)
        self.rib1 = self.rib2.copy()
        self.rib1.mirror()

        self.cell1 = Cell(self.rib1, self.rib2)
        self.cell2 = Cell(self.rib2, self.rib3)


    def test_show_cell(self, num=10):
        #print(self.rib1.profile_2d.x_values)
        ribs = [self.cell1.midrib(x*1./num) for x in range(num)]
        ribs += [self.cell2.midrib(x*1./num) for x in range(num)]
        Graph.Graphics([Graph.Line(x.data) for x in ribs]+[Graph.Line(self.rib1.profile_3d.data)])
