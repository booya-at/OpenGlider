import os
import math
import random
import sys
import unittest
from openglider.airfoil.parametric import BezierProfile2D
from openglider.vector import Polygon2D, PolyLine2D
import openglider.plots.marks

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
        self.profile.close()
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

    def test_show_points(self):
        nvek = PolyLine2D(self.profile.normvectors)

        def draw_x(x):
            ik = self.profile(x)
            p = self.profile[ik]
            n = nvek[ik] * 0.02
            return openglider.plots.marks.cross(p-n, p+n, rotation=True)

        x_pos = [-0.9,-.2, .3, .8]
        nodes = [draw_x(x) for x in x_pos]

        elems = [openglider.graphics.Line(self.profile.data)]
        for n in nodes:
            for l in n:
                elems.append(openglider.graphics.Line(l))

        openglider.graphics.Graphics2D(elems)


if __name__ == "__main__":
    unittest.main()