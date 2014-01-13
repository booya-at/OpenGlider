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
import os
import math
import sys

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.Profile import Profile2D
from openglider.Cells import BasicCell
from openglider.Ribs import Rib
import openglider.Graphics as Graph
from openglider.Utils.Ballooning import BallooningBezier

import numpy



a = Profile2D()
#a.importdat(os.path.dirname(os.path.abspath(__file__)) + "/testprofile.dat")
a.compute_naca(naca=2412, numpoints=200)
# #a._rootprof.normalize()
# #a.numpoints = 25
#a.numpoints = 40
ballooning = BallooningBezier()
balloon = [ballooning(i) for i in a.x_values]

r1 = Rib(a, ballooning, [0., 0.12, 0], 1., 20 * math.pi / 180, 2 * math.pi / 180, 0, 7.)
r3 = Rib(a, ballooning, [0.2, 0.3, -0.1], 0.8, 30 * math.pi / 180, 5 * math.pi / 180, 0, 7.)
r2 = r1.copy()
r2.mirror()
for i in [r1, r2, r3]:
    i.recalc()

cell = BasicCell(r2.profile_3d, r1.profile_3d, balloon)
cell2 = BasicCell(r1.profile_3d, r3.profile_3d, balloon)
cell.recalc()
cell2.recalc()

num = 20
ribs = [cell.midrib_basic_cell(x * 1. / num).data for x in range(num + 1)]
ribs += [cell2.midrib_basic_cell(x * 1. / num).data for x in range(num + 1)]
#G.Graphics3D([G.Line(r1.profile_3d.data),G.Line(r2.profile_3d.data),G.Line([[0.,0.,0.],[1.,0.,0.]]),G.Line([[0.,0.,0.],[0.,0.5,0.]])])
Graph.Graphics([Graph.Line(x) for x in ribs])
