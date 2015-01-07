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
import unittest
import sys
import os
import random

try:
    import openglider
except ImportError:
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider

import openglider.utils.bezier as bezier


class TestBezier(unittest.TestCase):
    def setUp(self):
        controlpoints = [[i, random.random()] for i in range(5)]
        self.bezier = bezier.BezierCurve(controlpoints)

    def test_get_value(self):
        val = random.random()
        self.assertAlmostEqual(self.bezier(val)[0], self.bezier(val)[0])
        self.assertAlmostEqual(self.bezier(val)[1], self.bezier(val)[1])

    def test_fit(self):
        to_fit = [[0, 0], [1, 1], [2, 0]]
        self.bezier = bezier.BezierCurve.fit(to_fit, numpoints=3)
        self.assertAlmostEqual(self.bezier.controlpoints[0][0], 0)
        self.assertAlmostEqual(self.bezier.controlpoints[0][1], 0)
        self.assertGreater(self.bezier(0.5)[1], 0)
        self.assertAlmostEqual(self.bezier.xpoint(1.)[1], 1)

    def test_length(self):
        self.bezier.controlpoints = [[0, 0], [2, 0]]
        self.assertAlmostEqual(self.bezier.get_length(10), 2.)




