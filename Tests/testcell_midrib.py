#!/bin/python2

__author__ = 'simon'
from openglider.Profile import Profile2D
from openglider.Cells import Cell
from openglider.Ribs import Rib
import os
import math
import openglider.Graphics as Graph
from openglider.Utils.Ballooning import BallooningBezier
from openglider.Profile._Classes import MiniRib


a = Profile2D()
a.importdat(os.path.dirname(os.path.abspath(__file__))+"/test.dat")
#a.Numpoints = 400

midribs = [
    #MiniRib(0.2, 0.8, 1),
    MiniRib(0.5, 0.7, 1),
    #MiniRib(0.8, 0.8, 1),
]

b1 = BallooningBezier()
b2 = BallooningBezier()
b2.Amount *= 0.8


r2 = Rib(a, b1, [0.12, 0, 0], 1., 20*math.pi/180, 2*math.pi/180, 0, 7)
r1 = r2.copy()
r1.mirror()
r3 = Rib(a, b2, [0.3, 0.2, -0.1], 0.8, 30*math.pi/180, 5*math.pi/180, 0, 7)

for i in [r1, r2, r3]:
    i.recalc()

cell1 = Cell(r1, r2, midribs)
cell1.recalc()
cell2 = Cell(r2, r3, [])
cell2.recalc()


num = 40
#ribs = [cell1.midrib(x*1./num) for x in range(num+1)]
#ribs += [cell2.midrib(x*1./num) for x in range(num+1)]
#G.Graphics3D([G.Line(r1.profile_3d.data),G.Line(r2.profile_3d.data),G.Line([[0.,0.,0.],[1.,0.,0.]]),G.Line([[0.,0.,0.],[0.,0.5,0.]])])
#Graph.Graphics3D([Graph.Line(x.data) for x in ribs])
ribs = []
for x in range(num+1):
    ribs += cell1.midrib(x*1./num).data
for x in range(1, num+1):
    ribs += cell2.midrib(x*1./num).data

polygons = []
points = a.Numpoints

for i in range(2*num):
    for j in range(points-1):
        polygons.append(Graph.Polygon([i*points+j, i*points+j+1, (i+1)*points+j+1, (i+1)*points+j]))
Graph.Graphics3D(polygons, ribs)
