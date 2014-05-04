
import sys
import os
import unittest
import numpy

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.graphics import Graphics2D, Line, Green, Red
import openglider.airfoil
from openglider.utils.bezier import BezierCurve


class TestMarks(unittest.TestCase):
    def setUp(self):
        self.curve = BezierCurve()
        self.points = [[0., 0.], [0.5, 0.5], [1., 0.]]
        self.profile = openglider.airfoil.Profile2D()
        self.profile.compute_naca(9012, numpoints=100)

    def test_bezier_fit(self):
        nose_ind = self.profile.noseindex
        upper = BezierCurve()
        lower = BezierCurve()
        upper.fit(self.profile.data[:nose_ind+1],numpoints=10)
        lower.fit(self.profile.data[nose_ind:], numpoints=10)

        Graphics2D([
            Red,
            Line(self.profile.data),
            Green,
            Line(map(upper, numpy.linspace(0, 1, 100))),
            Line(map(lower, numpy.linspace(0, 1, 100)))
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


if __name__ == "__main__":
    unittest.main(verbosity=2)