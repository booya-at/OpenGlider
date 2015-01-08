import os
import math
import random
import sys
import unittest
from openglider.airfoil.parametric import BezierProfile2D
import openglider.vector
from openglider.vector.polygon import Polygon2D

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
        prof = random.randint(1, 9999)
        self.profile = Profile2D.compute_naca(prof, 200)
        #self.airfoil.importdat(proffile)

    def test_allowance(self):
        prof = self.profile.copy()
        prof.add_stuff(random.random()*0.1)
        prof = Polygon2D(prof.data)
        prof.close()
        openglider.graphics.Graphics([openglider.graphics.Line(prof.data),
                                      openglider.graphics.Line(self.profile.data)])

    def test_fit(self):
        profile2 = BezierProfile2D(self.profile.data)
        profile2.apply_splines()
        profile2.move([0,2])
        openglider.graphics.Graphics([openglider.graphics.Line(self.profile.data),
                                      openglider.graphics.Red,
                                      openglider.graphics.Line(profile2.data)])
