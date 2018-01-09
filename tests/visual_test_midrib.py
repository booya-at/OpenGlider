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
from __future__ import division
import math
import sys
import os

import numpy as np

from openglider.glider.cell.cell import Cell
from openglider.glider.rib.minirib import MiniRib
from openglider.glider.rib.rib import Rib


try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.airfoil import Profile2D
import openglider.graphics as Graph
from openglider.glider.ballooning import BallooningBezier


profile = Profile2D.import_from_dat(os.path.dirname(os.path.abspath(__file__)) + "/common/testprofile.dat")
#a.Numpoints = 40

midribs = [
    #MiniRib(0.2, 0.8, 1),
    MiniRib(0.5, 0.7, 1),
    #MiniRib(0.8, 0.8, 1),
]

b1 = BallooningBezier()
b2 = BallooningBezier()
b2.amount_maximal *= 0.8

r2 = Rib(profile, [0, 0.12, 0], 1., 20 * math.pi / 180, 2 * math.pi / 180, 0, 7)
r1 = r2.copy()
r1.mirror()
r3 = Rib(profile, [0.2, 0.3, -0.1], 0.8, 30 * math.pi / 180, 5 * math.pi / 180, 0, 7)


cell1 = Cell(r1, r2, b1, midribs)
cell2 = Cell(r2, r3, b2, [])

num = 20
#ribs = [cell1.midrib(x*1./num) for x in range(num+1)]
#ribs += [cell2.midrib(x*1./num) for x in range(num+1)]
#G.Graphics3D([G.Line(r1.profile_3d.data),G.Line(r2.profile_3d.data),G.Line([[0.,0.,0.],[1.,0.,0.]]),G.Line([[0.,0.,0.],[0.,0.5,0.]])])
#Graph.Graphics3D([Graph.Line(x.data) for x in ribs])
ribs = []
for x in range(num + 1):
    ribs.append(cell1.midrib(x * 1. / num).data)
for x in range(1, num + 1):
    ribs.append(cell2.midrib(x * 1. / num).data)
ribs = np.concatenate(ribs)
polygons = []
points = profile.numpoints

for i in range(2 * num):
    for j in range(points - 1):
        polygons.append(
            Graph.Polygon([i * points + j, i * points + j + 1, (i + 1) * points + j + 1, (i + 1) * points + j]))
polygons.append(Graph.Axes(size=0.3))
Graph.Graphics3D(polygons, ribs)
