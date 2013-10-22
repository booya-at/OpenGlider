__author__ = 'simon'

import numpy
from Utils.Bezier import BezierCurve
#TODO ballooning -> upper: beziercurve, lower beziercurve, mapx, amount (total(integral),maximal)
class Ballooning(object):
    def __init__(self, points=[]):
        self.upper=BezierCurve(points[0])
        self.lower=BezierCurve(points[1])

    def mapx(self,xvals):
        return 
