import numpy as np
from scipy.misc import comb
import scipy.interpolate
from scipy.optimize import bisect as findroot


class BezierCurve(object):
    def __init__(self, points=[[0, 0], [1, 10], [2, 0]]):
        """Bezier Curve represantative
        http://en.wikipedia.org/wiki/Bezier_curve#Generalization"""
        self._setcontrolpoints(points)

    def __call__(self, value):
        if 0 <= value <= 1:
            return self._BezierFunction(value)
        else:
            ValueError("value must be in the range (0,1) for xvalues use xpoint-function")

    def _setnumpoints(self, num):
        if not num == self.NumPoints:
            self._BezierBase = bernsteinbase(num)

    def _getnumpoints(self):
        try:
            leng = len(self._BezierBase)
        except AttributeError:
            leng = 0
        return leng

    def _setcontrolpoints(self, points):
        self.NumPoints=len(points)
        self._controlpoints = points
        self._BezierFunction = bezierfunction(points, self._BezierBase)

    def _getcontrolpoints(self):
        return self._controlpoints

    def xpoint(self, x):
        root = findroot(lambda x2: self._BezierFunction(x2)[0]-x, 0, 1)
        return self._BezierFunction(root)

    def ypoint(self, y):
        root = findroot(lambda y2: self._BezierFunction(y2)[1]-y, 0, 1)
        return self._BezierFunction(root)

    def fit(self, data, numpoints=None):
        if numpoints:
            self.NumPoints = numpoints
        self.ControlPoints = fitbezier(data, self._BezierBase)

    def interpolation(self, num=100):
        x = []
        y = []
        for i in range(num):
            point = self(i*1./(num-1))
            x.append(point[0])
            y.append(point[1])
        return scipy.interpolate.interp1d(x, y)

    ControlPoints = property(_getcontrolpoints, _setcontrolpoints)
    NumPoints = property(_getnumpoints, _setnumpoints)


##############################FUNCTIONS


def bernsteinbase(d):
    def bsf(n):
        return lambda x: comb(d-1, n)*(x**n)*((1-x)**(d-1-n))
    return [bsf(i) for i in range(d)]


def bezierfunction(points, base=None):
    """"""
    if not base:
        base = bernsteinbase(len(points))
    def func(x):
        val = np.zeros(len(points[0]))
        for i in range(len(points)):
            fakt = base[i](x)
            v = np.array(points[i])*fakt
            val = val+v
        return val
    return func


def fitbezier(points, base=bernsteinbase(3), start=True, end=True):
    """Fit to a given set of points with a certain number of spline-points (default=3)
    if start (/ end) is True, the first (/ last) point of the Curve is included"""
    matrix = np.matrix([[base[column](row*1./(len(points)-1)) for column in range(len(base))] for row in range(len(points))])
    matrix = np.linalg.pinv(matrix)
    out = np.array(matrix*points)
    if start:
        out[0] = points[0]
    if end:
        out[-1] = points[-1]
    return out
