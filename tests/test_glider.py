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
    import openglider


testfolder = os.path.dirname(os.path.abspath(__file__))
importpath = testfolder + '/demokite.ods'

class GliderTestClass(unittest.TestCase):
    def setUp(self, complete=True):
        self.glider = openglider.glider.Glider.import_geometry(path=importpath)

    def assertEqualGlider(self, glider):
        self.assertEqual(len(self.glider.ribs), len(glider.ribs))
        self.assertEqual(len(self.glider.cells), len(glider.cells))
        for rib_1, rib_2 in zip(self.glider.ribs, glider.ribs):
            # test profile_3d this should include align, profile,...
            for xyz_1, xyz_2 in zip(rib_1.profile_3d, rib_2.profile_3d):
                for _p1, _p2 in zip(xyz_1, xyz_2):
                    self.assertAlmostEqual(_p1, _p2)
        # todo: expand test: lines, diagonals,...


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
        ar = random.random() * 10
        area_bak = self.glider.area
        self.glider.aspect_ratio = ar
        self.glider.aspect_ratio = ar  # -> Do it twice and its precise
        self.assertAlmostEqual(area_bak, self.glider.area)
        self.assertAlmostEqual(ar, self.glider.aspect_ratio, 3)

    def test_scale(self):
        ar = self.glider.aspect_ratio
        self.glider.scale(random.random()*10)
        self.assertAlmostEqual(ar, self.glider.aspect_ratio)

    def test_flatten(self):
        y = random.random()*len(self.glider.cells)
        self.glider.get_midrib(y).flatten()


if __name__ == '__main__':
    unittest.main(verbosity=2)