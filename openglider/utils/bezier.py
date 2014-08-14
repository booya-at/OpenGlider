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
        return {'controlpoints': [p.tolist() for p in self.controlpoints]}

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
    def numpoints(self, num_ctrl, num_points=50):
        if not num_ctrl == self.numpoints:
            base = bernsteinbase(num_ctrl)
            self.controlpoints = fitbezier([self(i) for i in numpy.linspace(0, 1, num_points)], base)

    @cached_property('numpoints')
    def _bezierbase(self):
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

    @classmethod
    def fit(cls, data, numpoints=None):
        # wenn numpoints is none -> eigene anzahl an kontrollpunkten verwenden
        bezier = cls()
        if numpoints:
            bezier.numpoints = numpoints
        bezier.controlpoints = fitbezier(data, bezier._bezierbase)
        return bezier

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
    if not start and not end:
        matrix = numpy.linalg.pinv(matrix)
        out = numpy.array(matrix * points)
        return out
    else:
        A1=numpy.array(matrix)
        A2=[]
        points2=[]
        points1 = numpy.array(points)
        solution = []
        
        if start:
            # add first column to A2 and remove first column of A1
            A2.append(A1[:, 0])
            A1 = A1[:, 1:]
            points2.append(points[0])
            points1 = points1[1:]

        if end:
            # add last column to A2 and remove last column of A1
            A2.append(A1[:, -1])
            A1 = A1[:, :-1]
            points2.append(points[-1])
            points1 = points[:-1]
        A1_inv = numpy.linalg.inv(numpy.dot(A1.T, A1))
        A2 = numpy.array(A2).T
        points1 = numpy.array(points).T
        points2 = numpy.array(points2).T
        for dim, _ in enumerate(points1):
            rhs1 = numpy.array(A1.T.dot(points1[dim]))
            rhs2 = numpy.array((A1.T.dot(A2)).dot(points2[dim])).T
            solution.append(numpy.array(A1_inv.dot(rhs1 - rhs2)))
        solution = (numpy.matrix(solution).T).tolist()
        if start:
            solution.insert(0, points[0])
        if end:
            solution.append(points[-1])
        return solution

if __name__ == "__main__":
    a = BezierCurve([[0,0], [10,10], [20,20]])
    a.numpoints = 4
    print(a.controlpoints)
    print(BezierCurve.fit([[0,0],[10,4],[20,0]]).controlpoints)
