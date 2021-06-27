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
import random
import unittest
import os
import math
import sys
import numpy as np
import euklid

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.graphics import Graphics, Line, Red, Point, Blue


class TestLayer(unittest.TestCase):
    def setUp(self, numpoints=100):
        p0 = [0.,0.,0.]
        v1 = [1.,0.,0.]
        v2 = [0.,1.,0.]
        self.layer = euklid.plane.Plane(p0, v1, v2)

    def testCut(self):
        p1 = np.array([0., 0., -1.])
        p2 = np.array([1., 1., 1.])
        res = self.layer.cut(p1, p2)[2]
        openglider.graphics.Graphics([openglider.graphics.Line([p2, p1]),
                  Blue,
                  Line([self.layer.p0, self.layer.p0+self.layer.v1]),
                  Line([self.layer.p0, self.layer.p0+self.layer.v2]),
                  Red,
                  Point([res])
                  ])

    def testProjection(self):
        p1 = np.array([1., 1., -1.])
        res = self.layer.projection(p1)
        res = self.layer.point(*res)
        openglider.graphics.Graphics([openglider.graphics.Line([p1, self.layer.p0]),
                                      Blue,
                                      Line([self.layer.p0, self.layer.p0+self.layer.v1]),
                                      Line([self.layer.p0, self.layer.p0+self.layer.v2]),
                                      Red,
                                      Line([self.layer.p0, self.layer.p0 + res])
        ])