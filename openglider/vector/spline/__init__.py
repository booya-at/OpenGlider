from __future__ import division

import numpy
import scipy
from scipy.optimize import bisect as findroot

from openglider.utils.cache import HashedList
from openglider.vector import norm, mirror2D_x
from openglider.vector.spline.bezier import BernsteinBase


class BezierCurve(HashedList):
    basefactory = BernsteinBase

    def __init__(self, controlpoints=None):
        """
        Bezier Curve representative
        http://en.wikipedia.org/wiki/Bezier_curve#Generalization
        """
        super(BezierCurve, self).__init__(controlpoints)

    def __json__(self):
        return {'controlpoints': [p.tolist() for p in self.controlpoints]}

    @classmethod
    def __from_json__(cls, controlpoints):
        return cls(controlpoints)

    def __call__(self, value):
        dim = len(self.data[0])
        assert 0 <= value <= 1, "value must be in the range (0,1), not {}".format(value)

        val = numpy.zeros(dim)
        base = self.basefactory(len(self.data))
        for i, point in enumerate(self.data):
            val += point * base[i](value)
        return val

    @property
    def numpoints(self):
        try:
            return len(self.controlpoints)
        except TypeError:
            return 0

    @numpoints.setter
    def numpoints(self, num_ctrl, num_points=50):
        if not num_ctrl == self.numpoints:
            data = [self(i) for i in numpy.linspace(0, 1, num_points)]
            self.controlpoints = self.fit(data, num_ctrl).data

    @property
    def controlpoints(self):
        return self._data

    @controlpoints.setter
    def controlpoints(self, points):
       self.data = points

    def xpoint(self, x):
        root = findroot(lambda x2: self.__call__(x2)[0] - x, 0, 1)
        return self.__call__(root)

    def ypoint(self, y):
        root = findroot(lambda y2: self.__call__(y2)[1] - y, 0, 1)
        return self.__call__(root)

    # @classmethod
    # def fit_(cls, data, numpoints=3):
    #     bezier = cls([[0,0] for __ in range(numpoints)])
    #     bezier._data = numpy.array(fitbezier(data, bezier._bezierbase))
    #     return bezier

    @classmethod
    def fit(cls, points, numpoints=5, start=True, end=True):
        """
        Fit to a given set of points with a certain number of spline-points (default=3)
        if start (/ end) is True, the first (/ last) point of the Curve is included
        """
        base = cls.basefactory(numpoints)
        matrix = numpy.matrix(
            [[base[column](row * 1. / (len(points) - 1))
                for column in range(len(base))]
                    for row in range(len(points))])

        if not start and not end:
            matrix = numpy.linalg.pinv(matrix)
            out = numpy.array(matrix * points)
            return out
        else:
            A1 = numpy.array(matrix)
            A2 = []
            points2 = []
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
            for dim, point in enumerate(points1):
                rhs1 = numpy.array(A1.T.dot(point))
                rhs2 = numpy.array((A1.T.dot(A2)).dot(points2[dim])).T
                solution.append(numpy.array(A1_inv.dot(rhs1 - rhs2)))
            solution = numpy.matrix(solution).T.tolist()
            if start:
                solution.insert(0, points[0])
            if end:
                solution.append(points[-1])

        return cls(solution)

    def interpolation(self, num=100, **kwargs):
        x, y = self.get_sequence(num).T
        return scipy.interpolate.interp1d(x, y, **kwargs)

    def interpolate_3d(self, num=100, axis=0, bounds_error=False):
        """
        Return scipy interpolation for a given axis (x=0, y=1
        """
        data = self.get_sequence(num).T
        return scipy.interpolate.interp1d(data[axis], data, bounds_error=bounds_error)

    def get_sequence(self, num=50):
        data = []
        for i in range(num):
            point = self(i / (num - 1))
            data.append(point)
        return numpy.array(data)

    def get_length(self, num):
        seq = self.get_sequence(num=num)
        out = 0.
        for i, s in enumerate(seq[1:]):
            out += norm(s - seq[i])
        return out


class SymmetricBezier(BezierCurve):
    def __init__(self, controlpoints=None, mirror=None):
        self._mirror = mirror or mirror2D_x
        super(SymmetricBezier, self).__init__(controlpoints=controlpoints)

    @classmethod
    def __from_json__(cls, controlpoints):
        sm = cls()
        sm.controlpoints = controlpoints
        return sm

    @property
    def controlpoints(self):
        return self._data[self.numpoints:]

    @controlpoints.setter
    def controlpoints(self, controlpoints):
        self.data = numpy.array(self._mirror(controlpoints)[::-1] + controlpoints)

    @property
    def numpoints(self):
        return len(self._data) // 2

    @numpoints.setter
    def numpoints(self, num_ctrl, num_points=50):
        if not num_ctrl == self.numpoints:
            num_ctrl *= 2
            data = [self(i) for i in numpy.linspace(0, 1, num_points)]
            self._data = BezierCurve.fit(data, num_ctrl).data

    @classmethod
    def fit(cls, data, numpoints=3):
        return super(SymmetricBezier, cls).fit(data, numpoints=numpoints*2)



