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

import common
import openglider
from openglider.glider.rib import Rib



class TestRib(unittest.TestCase):

    def setUp(self):
        naca = random.randint(1, 9999)
        numpoints = random.randint(10,200)
        self.prof = openglider.airfoil.Profile2D.compute_naca(naca, numpoints)
        self.rib = Rib(self.prof,
                       startpoint=[random.random(), random.random(), random.random()],
                       chord=random.random(),
                       arcang=random.random(),
                       aoa_absolute=random.random(),
                       glide=random.random()*10)


    def test_normvectors(self):
        normvectors = self.rib.normvectors

    def test_align(self):
        first = self.rib.pos
        second = self.rib.align([0, 0, 0])
        for i in range(3):
            self.assertAlmostEqual(first[i], second[i])

    def test_align_scale(self):
        prof1 = [self.rib.align(p) for p in self.rib.profile_2d]
        _prof2 = self.rib.profile_2d.copy()
        _prof2.scale(self.rib.chord)
        prof2 = [self.rib.align(p, scale=False) for p in _prof2]


        for p1, p2 in zip(prof1, prof2):
            self.assertAlmostEqual(p1[0], p2[0])
            self.assertAlmostEqual(p1[1], p2[1])
            self.assertAlmostEqual(p1[2], p2[2])



