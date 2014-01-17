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
import random
import os
import sys
import unittest

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider import glider

test_folder = os.path.dirname(os.path.abspath(__file__))


class TestGlider(unittest.TestCase):
    #def __init__(self):
    #    unittest.TestCase.__init__(self)
    def setUp(self):
        self.glider = glider.Glider()
        self.glider.import_geometry(test_folder + '/demokite.ods')

    def test_numpoints(self):
        numpoints = random.randint(1, 100)*2+1
        self.glider.numpoints = numpoints
        self.assertEqual(self.glider.numpoints, numpoints)

    def test_span(self):
        span = random.random() * 100
        self.glider.span = span
        self.assertAlmostEqual(self.glider.span, span)

    def test_area(self):
        area = random.random() * 100
        self.glider.recalc()
        self.glider.area = area
        self.glider.recalc()
        self.assertAlmostEqual(self.glider.area, area)

    def test_aspectratio(self):
        ar = random.random() * 10
        self.glider.recalc()
        area_bak = self.glider.area
        self.glider.aspect_ratio = ar
        self.glider.aspect_ratio = ar  # -> Do it twice and its precise
        self.glider.recalc()
        self.assertAlmostEqual(area_bak, self.glider.area)
        self.assertAlmostEqual(ar, self.glider.aspect_ratio, 3)

    def test_scale(self):
        self.glider.recalc()
        ar = self.glider.aspect_ratio
        self.glider.scale(random.random()*10)
        self.glider.recalc()
        self.assertAlmostEqual(ar, self.glider.aspect_ratio)

    def test_flatten(self):
        self.glider.recalc()
        y = random.random()*len(self.glider.cells)
        self.glider.get_midrib(y).flatten()


if __name__ == '__main__':
    unittest.main(verbosity=2)