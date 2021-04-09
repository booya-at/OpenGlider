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
import numpy as np
from openglider.vector.functions import norm, rotation_3d


__author__ = 'simon'
import unittest
import random


class TestVectorFunctions3D(unittest.TestCase):
    def setUp(self):
        self.vectors = [
            [random.random()+0.001 for _ in range(3)]
            for _ in range(100)
        ]

    def test_rotation_scale(self):
        angle = 2*random.random() - 1
        rot = rotation_3d(0, [1, 0, 0])
        for axis in self.vectors:
            rotation_matrix = rotation_3d(angle, axis)
            rot = rot.dot(rotation_matrix)
            for v in self.vectors:
                self.assertAlmostEqual(norm(rot.dot(v)), norm(v))
                self.assertAlmostEqual(norm(rotation_matrix.dot(v)), norm(v))

    def test_rotation_scale_2(self):
        rot = rotation_3d(0, [1,0,0])
        for axis in self.vectors:
            angle = 2*random.random() - 1
            scale = random.random()
            rotation_matrix = rotation_3d(angle, axis)
            rot = rot.dot(rotation_matrix)

            for v in self.vectors:
                p1 = rot.dot(np.array(v) * scale)
                p2 = rot.dot(v) * scale
                for i in range(3):
                    self.assertAlmostEqual(p1[i], p2[i])




if __name__ == '__main__':
    unittest.main(verbosity=2)