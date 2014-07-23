#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.


import numpy
from scipy.misc import comb
import scipy.interpolate
from scipy.optimize import bisect as findroot
from openglider.utils.cache import cached_property, CachedObject

__ALL = ['BezierCurve']


class BezierCurve(CachedObject):
    def __init__(self, controlpoints=None):
        """Bezier Curve represantative
        http://en.wikipedia.org/wiki/Bezier_curve#Generalization"""
        #self._BezierBase = self._BezierFunction = self._controlpoints = None
        self._controlpoints = None
        if controlpoints is None:
            controlpoints = [[0, 0], [1, 10], [2, 0]]
        self.controlpoints = controlpoints

    def __json__(self):
        return {'controlpoints': self.controlpoints}

    def __call__(self, value):
        if 0 <= value <= 1:
            val = numpy.zeros(len(self.controlpoints[0]))
            for i, point in enumerate(self.controlpoints):
                fakt = self._bezierbase[i](value)
                #print(fakt, point, val)
                val += point * fakt
            return val
        else:
            ValueError("value must be in the range (0,1) for xvalues use xpoint-function")

    @property
    def numpoints(self):
        try:
            return len(self.controlpoints)
        except TypeError:
            return 0

    @numpoints.setter
    def numpoints(self, num):
        # TODO: fit
        pass
        #if not num == self.numpoints:
        #    self._BezierBase = bernsteinbase(num)

    @cached_property('numpoints')
    def _bezierbase(self):
        d = self.numpoints
        return bernsteinbase(self.numpoints)
        #return [lambda x: comb(d - 1, n) * (x ** n) * ((1 - x) ** (d - 1 - n)) for n in range(d)]

    @property
    def controlpoints(self):
            return self._controlpoints

    @controlpoints.setter
    def controlpoints(self, points):
        #self.numpoints = len(points)
        self._controlpoints = [numpy.array(p) for p in points]
        #self._BezierFunction = bezierfunction(points, self._BezierBase)

    def xpoint(self, x):
        root = findroot(lambda x2: self.__call__(x2)[0] - x, 0, 1)
        return self.__call__(root)

    def ypoint(self, y):
        root = findroot(lambda y2: self.__call__(y2)[1] - y, 0, 1)
        return self.__call__(root)

    def fit(self, data, numpoints=None):
        if numpoints:
            self.numpoints = numpoints
        self.controlpoints = fitbezier(data, self._bezierbase)

    def interpolation(self, num=100):
        x = []
        y = []
        for i in range(num):
            point = self(i * 1. / (num - 1))
            x.append(point[0])
            y.append(point[1])
        return scipy.interpolate.interp1d(x, y)

    def interpolate_3d(self, num=100, xyz=0):
        x = []
        data = []
        for i in range(num):
            point = self(i * 1. / (num - 1))
            x.append(point[xyz])
            data.append(point)
        print(numpy.transpose(data))
        return scipy.interpolate.interp1d(x, numpy.transpose(data),bounds_error=False)

    def get_sequence(self, num=50):
        x = []
        y = []
        for i in range(num):
            point = self(i * 1. / (num - 1))
            x.append(point[0])
            y.append(point[1])
        return([x, y])

##############################FUNCTIONS


def bernsteinbase(d):
    def bsf(n):
        return lambda x: comb(d - 1, n) * (x ** n) * ((1 - x) ** (d - 1 - n))

    return [bsf(i) for i in range(d)]


def bezierfunction(points, base=None):
    """"""
    if not base:
        base = bernsteinbase(len(points))

    def func(x):
        val = numpy.zeros(len(points[0]))
        for i in range(len(points)):
            fakt = base[i](x)
            v = numpy.array(points[i]) * fakt
            val += v
        return val

    return func


def fitbezier(points, base=bernsteinbase(3), start=True, end=True):
    """Fit to a given set of points with a certain number of spline-points (default=3)
    if start (/ end) is True, the first (/ last) point of the Curve is included"""
    matrix = numpy.matrix(
        [[base[column](row * 1. / (len(points) - 1)) for column in range(len(base))] for row in range(len(points))])
    matrix = numpy.linalg.pinv(matrix)
    out = numpy.array(matrix * points)
    if start:
        out[0] = points[0]
    if end:
        out[-1] = points[-1]
    return out
