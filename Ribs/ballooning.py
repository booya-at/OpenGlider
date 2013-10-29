__author__ = 'simon'

import numpy
from Utils.Bezier import BezierCurve
#TODO ballooning -> amount (total(integral),maximal)
class Ballooning(object):
    def __init__(self, points=[[[0, 0], [0.2, 0.04], [0.8, 0.04], [1, 0]],
                               [[0, 0], [0.2, -0.04], [0.8, -0.04], [1, 0]]]):
        self.upper = BezierCurve(points[0])
        self.lower = BezierCurve(points[1])

    def __getitem__(self, xval):
        if -1 <= xval < 0:
            return self.upper.xpoint(-xval)
        elif 0<= xval <= 1:
            return self.lower.xpoint(xval)
        else:
            ValueError("Ballooning only between -1 and 1")

    def mapx(self, xvals):
        return [self[i] for i in xvals]

    def amount_maximal(self):
        pass

    def amount_integral(self):
        pass

    def amount_set(self,amount):
        factor = float(amount)/self.Amount
        self.upper.ControlPoints = [i*[1, factor] for i in self.upper.ControlPoints]
        self.lower.ControlPoints = [i*[1, factor] for i in self.lower.ControlPoints]

    Amount = property(amount_integral, amount_set)
