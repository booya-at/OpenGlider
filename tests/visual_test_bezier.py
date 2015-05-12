import random
import os
import unittest

import numpy

import sys
from openglider.vector import PolyLine


try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.graphics import Graphics2D, Graphics, Line, Green, Red, Blue
import openglider.airfoil
from openglider.vector.spline import *


class TestBezier(unittest.TestCase):
    def setUp(self):
        self.points = [[0., 0.], [0.5, 0.5], [1., 0.]]
        self.curve = Bezier(self.points)
        self.profile = openglider.airfoil.Profile2D.compute_naca(9012, numpoints=100)

    def test_bezier_fit(self):
        nose_ind = self.profile.noseindex
        upper = Bezier.fit(self.profile.data[:nose_ind+1], numpoints=5)
        lower = Bezier.fit(self.profile.data[nose_ind:], numpoints=5)

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
        Graphics([
            Red,
            Line(curve),
            Green,
            Line(lower.get_sequence(num=100)),
            Line(lower.controlpoints)
            ])

    def test_scale_bezier(self):
        curve1 = self.curve.get_sequence()
        factor = 1+random.random()
        curve2 = PolyLine(curve1)
        curve2.scale(factor)
        curve3 = self.curve.copy()
        curve3.controlpoints = [[p[0]*factor, -p[1]*factor] for p in curve3.controlpoints]
        Graphics([
            Line(curve1),
            Red,
            Line(curve3.get_sequence()),
            Blue,
            Line(curve2)
        ])


class TestBSpline(unittest.TestCase):
    def setUp(self):
        self.points = [[0., 0.], [0.5, 0.5], [1., 0.]]
        self.curve = BSpline(self.points)
        self.curve.basefactory = BSplineBase(2)
        self.profile = openglider.airfoil.Profile2D.compute_naca(9012, numpoints=100)

    def test_bspline_fit(self):
        nose_ind = self.profile.noseindex
        upper = self.curve.fit(self.profile.data[:nose_ind+1], numpoints=5)
        print(upper.basefactory.degree)
        lower = BSpline.fit(self.profile.data[nose_ind:], numpoints=5)

        Graphics2D([
            Red,
            Line(self.profile.data),
            Green,
            Line(map(upper, numpy.linspace(0, 1, 100))),
            Line(map(lower, numpy.linspace(0, 1, 100))),
            Line(upper.controlpoints),
            Line(lower.controlpoints)
            ])

    def test_bspline_interpolation(self):
        self.curve.controlpoints = self.points
        interpolation = self.curve.interpolation(num=20)
        func = lambda x: numpy.array([x, interpolation(x)])
        Graphics2D([
            Line(map(func, numpy.linspace(0, 1, 20))),
            Green,
            Line(self.points)
            ])

    def test_symmetric_bspline_fit(self):
        curve = [[x,numpy.cos(x)] for x in numpy.linspace(-1,1,30)]
        lower = SymmetricBSpline.fit(curve, numpoints=5)
        Graphics([
            Red,
            Line(curve),
            Green,
            Line(lower.get_sequence(num=100)),
            Line(lower.controlpoints)
            ])

    def test_scale_bspline(self):
        curve1 = self.curve.get_sequence()
        factor = 1+random.random()
        curve2 = PolyLine(curve1)
        curve2.scale(factor)
        curve3 = self.curve.copy()
        curve3.controlpoints = [[p[0]*factor, -p[1]*factor] for p in curve3.controlpoints]
        Graphics([
            Line(curve1),
            Red,
            Line(curve3.get_sequence()),
            Blue,
            Line(curve2)
        ])


if __name__ == "__main__":
    unittest.main(verbosity=1)