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
import sys
import os
try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.Utils import Ballooning


class TestBallooningBezier(unittest.TestCase):
    def setUp(self):
        self.ballooning = Ballooning.BallooningBezier()

    def test_multiplication(self):
        for i in range(100):
            factor = random.random()
            temp = self.ballooning * factor
            val = random.random()
            self.assertAlmostEqual(temp[val], self.ballooning[val] * factor)

    def test_addition(self):
        for i in range(100):
            val = random.random()
            self.assertAlmostEqual(2 * self.ballooning[val], (self.ballooning + self.ballooning)[val])


if __name__ == '__main__':
    unittest.main(verbosity=2)