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
__author__ = 'simon'
import unittest
from openglider.Profile import Profile2D
from test_Vector import *
import os.path

testfolder = os.path.dirname(os.path.abspath(__file__))


class TestProfile(unittest.TestCase):
    def setUp(self):
        self.prof = Profile2D()
        self.prof.importdat(testfolder + "/testprofile.dat")

    def test_numpoints(self):
        num = random.randint(4, 500)
        self.prof.numpoints = num
        self.assertEqual(num + 1 - num % 2, self.prof.numpoints)

    def test_profilepoint(self):
        x = random.random() * random.randint(-1, 1)
        self.assertAlmostEqual(abs(x), self.prof.profilepoint(x)[1][0])

    def test_multiplication(self):
        factor = random.random()
        other = self.prof * factor
        self.assertAlmostEqual(other.thickness, self.prof.thickness * factor)
        other *= 1. / factor
        self.assertAlmostEqual(other.thickness, self.prof.thickness)


if __name__ == '__main__':
    unittest.main(verbosity=2)
