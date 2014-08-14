
import sys
import os
import unittest
import numpy

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.graphics import Graphics2D, Graphics, Line, Green, Red
import openglider.airfoil
from openglider.utils.bezier import BezierCurve, SymmetricBezier


class TestMarks(unittest.TestCase):
    def setUp(self):
        self.curve = BezierCurve()
        self.points = [[0., 0.], [0.5, 0.5], [1., 0.]]
        self.profile = openglider.airfoil.Profile2D.compute_naca(9012, numpoints=100)

    def test_bezier_fit(self):
        nose_ind = self.profile.noseindex
        upper = BezierCurve.fit(self.profile.data[:nose_ind+1], numpoints=5)
        lower = BezierCurve.fit(self.profile.data[nose_ind:], numpoints=5)

        Graphics2D([
            Red,
            Line(self.profile.data),
            Green,
            Line(map(upper, numpy.linspace(0, 1, 100))),
            Line(map(lower, numpy.linspace(0, 1, 100))),
            Line(upper.controlpoints),
            Line(lower.controlpoints)
            ])

    def test_bezier_interpolation(self):
        self.curve.controlpoints = self.points
        interpolation = self.curve.interpolation(num=20)
        func = lambda x: numpy.array([x, interpolation(x)])
        Graphics2D([
            Line(map(func, numpy.linspace(0, 1, 20))),
            Green,
            Line(self.points)
            ])

    def test_symmetric_bezier_fit(self):
        curve = [[x,numpy.cos(x)] for x in numpy.linspace(-1,1,30)]
        lower = SymmetricBezier.fit(curve, numpoints=5)
        print(lower._controlpoints)
        Graphics([
            Red,
            Line(curve),
            Green,
            Line(numpy.transpose(lower.get_sequence(num=100))),
            Line(lower._controlpoints)
            ])


if __name__ == "__main__":
    unittest.main(verbosity=2)