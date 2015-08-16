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
import numpy
from openglider.vector import norm
from openglider.vector.text import Text

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.airfoil import Profile2D
from openglider.glider.cell.cell import Cell
from openglider.glider.rib.rib import Rib
import openglider.graphics as Graph
from openglider.glider.ballooning import BallooningBezier


class TestCell(unittest.TestCase):
    def setUp(self, numpoints=100):
        self.p1 = numpy.array([random.random(), random.random()])
        self.d = numpy.array([random.random(), random.random()]) * 100
        self.l = norm(self.d)
        self.p2 = self.p1 + self.d

    def show(self):
        baseline = Graph.Line([self.p1, self.p2])
        Graph.Graphics([baseline] + [Graph.Line(l) for l in self.text.get_vectors()])

    def test_unsized(self):
        self.text = Text("openglider", self.p1, self.p2)
        self.show()

    def test_align_left(self):
        self.text = Text("openglider", self.p1, self.p2, size=0.02*self.l)
        self.show()

    def test_align_right(self):
        self.text = Text("openglider", self.p1, self.p2, size=0.02*self.l, align="right")
        self.show()

    def test_align_center(self):
        self.text = Text("openglider", self.p1, self.p2, size=0.02*self.l, align="center")
        self.show()




if __name__ == "__main__":
    unittest.main(verbosity=2)