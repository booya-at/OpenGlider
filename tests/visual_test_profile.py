import os
import math
import random
import sys
import unittest
import openglider.vector

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider.airfoil import Profile2D
import openglider.graphics as Graph
from openglider.glider.ballooning import BallooningBezier


proffile = os.path.dirname(os.path.abspath(__file__)) + "/testprofile.dat"
#a.compute_naca(naca=2412, numpoints=200)


class ProfileTest(unittest.TestCase):
    def setUp(self):
        self.profile = Profile2D()
        prof = random.randint(1, 9999)
        self.profile.compute_naca(prof, 200)
        #self.airfoil.importdat(proffile)

    def test_allowance(self):
        prof = self.profile.copy()
        prof.add_stuff(random.random()*0.1)
        prof = openglider.vector.Polygon2D(prof.data)
        prof.close()
        openglider.graphics.Graphics([openglider.graphics.Line(prof.data),
                                      openglider.graphics.Line(self.profile.data)])
