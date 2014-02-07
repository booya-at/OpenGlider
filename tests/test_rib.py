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
from openglider.glider.ribs import Rib

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider


class TestRib(unittest.TestCase):

    def setUp(self):
        self.prof = openglider.Profile2D()
        naca = random.randint(1, 9999)
        self.prof.compute_naca(naca, random.randint(10,200))
        self.rib = Rib(self.prof,
                       startpoint=[random.random(), random.random(), random.random()],
                       size=random.random(),
                       arcang=random.random(),
                       aoa=random.random(),
                       glide=random.random()*10)
        self.rib.recalc()


    def test_normvectors(self):
        normvectors = self.rib.normvectors()

    def test_align(self):
        first = self.rib.pos
        second = self.rib.align([0, 0, 0])
        for i in range(3):
            self.assertAlmostEqual(first[i], second[i])



