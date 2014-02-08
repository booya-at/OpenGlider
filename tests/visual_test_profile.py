import os
import math
import random
import sys
import unittest
import openglider.Vector

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.Profile import Profile2D
import openglider.Graphics as Graph
from openglider.glider.ballooning import BallooningBezier


a = Profile2D()
#a.importdat(os.path.dirname(os.path.abspath(__file__)) + "/testprofile.dat")
a.compute_naca(naca=2412, numpoints=200)


class ProfileTest(unittest.TestCase):
    def setUp(self):
        self.profile = Profile2D()
        prof = random.randint(1, 9999)
        self.profile.compute_naca(prof, 200)

    def test_allowance(self):
        prof = self.profile.copy()
        prof.add_stuff(random.random()*0.1)
        prof = openglider.Vector.Polygon2D(prof.data)
        prof.close()
        openglider.Graphics.Graphics([openglider.Graphics.Line(prof.data),
                                      openglider.Graphics.Line(self.profile.data)])
