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
from __future__ import division

import unittest
import random
import time

from common import openglider
import openglider.utils.bezier as bezier


class TestBezier(unittest.TestCase):
    def setUp(self):
        controlpoints = [[i, random.random()] for i in range(15)]
        self.bezier = bezier.BezierCurve(controlpoints)

    def test_consistency(self):
        numpoints = 200
        data = [i/numpoints for i in range(numpoints+1)]
        for val in data:
            p1= self.bezier.call(val)
            p2=self.bezier(val)
            self.assertAlmostEqual(p1[0], p2[0], 0)
            self.assertAlmostEqual(p1[1], p2[1], 0)

    def test_get_value(self):
        val = random.random()
        self.assertAlmostEqual(self.bezier(val)[0], self.bezier(val)[0])
        self.assertAlmostEqual(self.bezier(val)[1], self.bezier(val)[1])

    def test_fit(self):
        num = len(self.bezier.controlpoints)
        to_fit = self.bezier.get_sequence()
        bezier2 = bezier.BezierCurve.fit(to_fit, numpoints=num)
        for p1, p2 in zip(self.bezier.controlpoints, bezier2.controlpoints):
            self.assertAlmostEqual(p1[0], p2[0], 0)
            self.assertAlmostEqual(p1[1], p2[1], 0)

    def test_length(self):
        self.bezier.controlpoints = [[0, 0], [2, 0]]
        self.assertAlmostEqual(self.bezier.get_length(10), 2.)

    def test_speed(self, num=100):
        time1 = time.time()
        for _ in range(num):
            self.bezier.controlpoints[0][1] = random.random()
            [self.bezier(i/(num-1)) for i in range(num)]
        time2 = time.time()
        for _ in range(num):
            self.bezier.controlpoints[0][1] = random.random()
            [self.bezier.call(i/(num-1)) for i in range(num)]
        print("call", time.time()-time2)
        print("__call__", time2-time1)




