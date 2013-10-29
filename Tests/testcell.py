__author__ = 'simon'
from openglider.Profile import Profile2D
from openglider.Cells import BasicCell
from openglider.Ribs import Rib
import os
import math
import openglider.Graphics as G

a = Profile2D()
a.importdat(os.path.dirname(os.path.abspath(__file__))+"/test.dat")

r1 = Rib(a,[0.1,0,0],10*math.pi/180,5,0,7)

r2 = r1.copy()
r2.mirror()
print("jopjO")
for i in [r1,r2]:
    i.ReCalc()


cell=BasicCell(r1.profile_3d,r2.profile_3d,[.18 for i in range(len(r1.profile_3d.data))])

ribs=[cell.midrib(x*1./10) for x in range(11)]
G.Graphics3D([G.Line(r1.profile_3d.data),G.Line(r2.profile_3d.data),G.Line([[0.,0.,0.],[1.,0.,0.]]),G.Line([[0.,0.,0.],[0.,0.5,0.]])])
G.Graphics3D([G.Line(x.data) for x in ribs])