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
import unittest

from common import *
import openglider.glider


class GliderTestClass(TestCase):
    def setUp(self, complete=True):
        self.glider = self.import_glider()


class TestGlider(GliderTestClass):
    #def __init__(self):
    #    unittest.TestCase.__init__(self)

    def test_numpoints(self):
        numpoints = random.randint(1, 100)*2+1
        self.glider.profile_numpoints = numpoints
        self.assertEqual(self.glider.profile_numpoints, numpoints)

    def test_span(self):
        span = random.random() * 100
        self.glider.span = span
        self.assertAlmostEqual(self.glider.span, span)

    def test_area(self):
        area = random.random() * 100
        self.glider.area = area
        self.assertAlmostEqual(self.glider.area, area)

    def test_aspectratio(self):
        ar = random.randint(4, 15) + random.random()
        area_bak = self.glider.area
        for i in range(15):
            self.glider.aspect_ratio = ar  # -> Do some times and its precise
        self.assertAlmostEqual(area_bak, self.glider.area)
        self.assertAlmostEqual(ar, self.glider.aspect_ratio, 3)

    def test_scale(self):
        ar = self.glider.aspect_ratio
        self.glider.scale(random.random()*10)
        self.assertAlmostEqual(ar, self.glider.aspect_ratio)

    def test_flatten(self):
        y = random.random()*len(self.glider.cells)
        self.glider.get_midrib(y).flatten()

    def copy_complete(self):
        self.glider.copy_complete()


if __name__ == '__main__':
    unittest.main(verbosity=2)