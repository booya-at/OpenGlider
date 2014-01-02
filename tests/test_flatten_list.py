import os
import math
import openglider.Graphics
import openglider.Ribs
import openglider.Profile
from openglider.Utils.Ballooning import BallooningBezier
import openglider.plots
import numpy
__author__ = 'simon'


prof = openglider.Profile.Profile2D()
prof.importdat(os.path.dirname(os.path.abspath(__file__)) + "/testprofile.dat")

ballooning = BallooningBezier()
balloon = [ballooning(i) for i in prof.x_values]

r1 = openglider.Ribs.Rib(prof, ballooning, [0., 0.12, 0], 1., 20 * math.pi / 180, 2 * math.pi / 180, 0, 7.)
r2 = r1.copy()
r2.mirror()
r1.recalc()
r2.recalc()

left, right = openglider.plots.flatten_list(r2.profile_3d.data, r1.profile_3d.data)
ding = [numpy.array([0, 0]), numpy.array([1., 0])]

openglider.Graphics.Graphics([openglider.Graphics.Line(left), openglider.Graphics.Line(right)])

#[numpy.array([0,0]),numpy.array([1,0])