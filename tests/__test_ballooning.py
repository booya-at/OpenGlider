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
import random

from .common import openglider
from openglider.glider import ballooning


class TestBallooningBezier(unittest.TestCase):
    @classmethod
    def get_ballooning(cls):
        num = random.randint(10, 30)
        x_values = [i/(num-1) for i in range(num)]
        upper = [[x, random.random()*0.1] for x in x_values]
        lower = [[x, random.random()*0.1] for x in x_values]
        return ballooning.BallooningBezier(upper, lower)

    def setUp(self):
        self.ballooning = self.get_ballooning()

    def test_multiplication(self):
        for i in range(100):
            factor = random.random()
            temp = self.ballooning * factor
            val = random.random()
            self.assertAlmostEqual(temp[val], self.ballooning[val] * factor)

    def test_addition(self):
        num = 100
        x_values = [(i-num)/num for i in range(2*num+1)]
        b1 = self.get_ballooning()
        b2 = self.get_ballooning()
        mixed = b1 + b2
        for x in x_values:
            self.assertAlmostEqual(b1[x]+b2[x], mixed[x], places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)