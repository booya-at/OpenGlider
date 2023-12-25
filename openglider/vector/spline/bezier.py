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
from __future__ import division

import numpy as np

from openglider.utils.cache import HashedList
from openglider.vector import norm, Interpolation
from openglider.vector.transformation import Reflection
from openglider.utils import dualmethod


class _BernsteinFactory:
    def __init__(self):
        self.bases = {}

    def __call__(self, degree):
        """degree is the number of controlpoints"""
        if degree not in self.bases:

            def bsf(n):
                return (
                    lambda x: choose(degree - 1, n)
                    * (x**n)
                    * ((1 - x) ** (degree - 1 - n))
                )

            self.bases[degree] = [bsf(i) for i in range(degree)]

        return self.bases[degree]

    def __json__(self):
        return {}

    @classmethod
    def __from_json__(cls):
        return cls()


BernsteinBase = _BernsteinFactory()


class Bezier(HashedList):
    basefactory = BernsteinBase

    def __init__(self, controlpoints=None):
        """
        Bezier Curve representative
        http://en.wikipedia.org/wiki/Bezier_curve#Generalization
        """
        self._matrix = None
        super(Bezier, self).__init__(controlpoints)

    def __repr__(self):
        return self.__class__.__name__ + ":\n" + str(self.controlpoints)

    def __json__(self):
        spline_dict = {
            "controlpoints": [p.tolist() for p in self.controlpoints],
            "basefactory": self.basefactory,
        }
        return spline_dict

    @classmethod
    def __from_json__(cls, controlpoints, basefactory=None, degree=None):
        # for old interface we stored degree in the spline
        # in the new interface degree is stored in the basefactory
        # therefor there is no difference between a bezier with
        # a bspline factory or a bspline with the same basefactory

        ### remove: obsolete for new gliders
        if degree:
            from openglider.vector import BsplineBase

            basefactory = BsplineBase(degree)
        basefactory = basefactory or cls.basefactory
        ### remove end

        spline = cls(controlpoints)
        spline.basefactory = basefactory
        return spline

    def __call__(self, value):
        dim = len(self.data[0])
        assert 0 <= value <= 1, "value must be in the range (0,1), not {}".format(value)

        val = np.zeros(dim)
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
            data = [self(i) for i in np.linspace(0, 1, num_points)]
            self.fit(data, num_ctrl)

    def change_base(self, base, num_points=50):
        data = [self(i) for i in np.linspace(0, 1, num_points)]
        self.basefactory = base
        self._matrix = None
        self.fit(data, self.numpoints)

    @property
    def controlpoints(self):
        return self._data

    @controlpoints.setter
    def controlpoints(self, points):
        self.data = points

    @dualmethod
    def fit(self, points, numpoints=5, start=True, end=True):
        """
        Fit to a given set of points with a certain number of spline-points (default=3)
        if start (/ end) is True, the first (/ last) point of the Curve is included
        """
        base = self.basefactory(numpoints)
        matrix = np.matrix(
            [
                [
                    base[column](row * 1.0 / (len(points) - 1))
                    for column in range(len(base))
                ]
                for row in range(len(points))
            ]
        )

        if not start and not end:
            matrix = np.linalg.pinv(matrix)
            out = np.array(matrix * points)
            return out
        else:
            A1 = np.array(matrix)
            A2 = []
            points2 = []
            points1 = np.array(points)
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
            A1_inv = np.linalg.inv(np.dot(A1.T, A1))
            A2 = np.array(A2).T
            points1 = np.array(points).T
            points2 = np.array(points2).T
            for dim, point in enumerate(points1):
                rhs1 = np.array(A1.T.dot(point))
                rhs2 = np.array((A1.T.dot(A2)).dot(points2[dim])).T
                solution.append(np.array(A1_inv.dot(rhs1 - rhs2)))
            solution = np.matrix(solution).T.tolist()
            if start:
                solution.insert(0, points[0])
            if end:
                solution.append(points[-1])

        if type(self) == type:  # classmethod
            return self(solution)
        else:
            self.controlpoints = solution
            return self

    @dualmethod
    def constraint_fit(self, points, constraint):
        """constraint is a matrix in size of the controlpointmatrix
        constraint values have a value others are set to None
        points is [[x0,y0,z0], X1, X2, ...]"""

        # all points have same dimension
        dim = len(constraint[0])
        num_ctrl_pts = len(constraint)

        # create the base matrix:
        base = self.basefactory(num_ctrl_pts)
        matrix = np.array(
            [
                [
                    base[column](row * 1.0 / (len(points) - 1))
                    for column in range(len(base))
                ]
                for row in range(len(points))
            ]
        )

        # create the b vector for each dim
        b = np.array(list(zip(*points)))

        # fit
        solution = []
        constraints_T = list(zip(*constraint))
        for i in range(dim):
            constraints = [
                [index, val]
                for index, val in enumerate(constraints_T[i])
                if val != None
            ]
            solution.append(self.constraint_least_square_sol(matrix, b[i], constraints))
        if type(self) == type:
            return self(np.array(solution).transpose())
        else:
            self.controlpoints = np.array(solution).transpose()
            return self

    @staticmethod
    def constraint_least_square_sol(A, b, constraint):
        """return u for minimized |A.u-b| with u containing the constraint points.
        A(n x m)...matrix with n >= m + c_n (n=num_cols, m=num_rows, c_n=num_constraints)
        constraint: dict of "indices: value" couples  [[0, 1.], [10, 3.]]"""
        # create vector from the known values
        u_fix = np.zeros(A.shape[1])
        u_sol_index = list(range(len(u_fix)))
        u = np.zeros(A.shape[1])
        for key, val in constraint:
            u_fix[key] = val

        # A.T.dot(A).dot(u) == A.T.dot(b) - A.T.dot(A).dot(u_fix)
        rhs = A.T.dot(b) - ((A.T).dot(A)).dot(u_fix)
        mat = A.T.dot(A)
        for i, key in enumerate(constraint):
            mat = np.delete(mat, key[0] - i, 0)
            mat = np.delete(mat, key[0] - i, 1)
            rhs = np.delete(rhs, key[0] - i, 0)
            u_sol_index.pop(key[0] - i)
        u_sol = np.linalg.solve(mat, rhs.transpose())

        # insert the known values in the solution
        for i, index in enumerate(u_sol_index):
            u[index] = u_sol[i]
        for key, val in constraint:
            u[key] = val
        return u

    def interpolation(self, num=100, **kwargs):
        return Interpolation(self.get_sequence(num))

    def scale(self, x=1, y=1):
        self.controlpoints = [p * [x, y] for p in self.controlpoints]

    def get_matrix(self, num=50):
        num_points = len(self._data)
        if self._matrix is not None and self._matrix.shape == (num, num_points):
            return self._matrix
        else:
            self._matrix = np.ndarray([num, num_points])
            functions = self.basefactory(num_points)
            for row, value in enumerate(np.linspace(0, 1, num)):
                for col, foo in enumerate(functions):
                    self._matrix[row, col] = foo(value)
            return self._matrix

    def get_sequence(self, num=None):
        if num is None:
            if self._matrix is not None:
                num = self._matrix.shape[0]
            else:
                num = 50  # default
        return np.dot(self.get_matrix(num), self._data)

    def get_length(self, num):
        seq = self.get_sequence(num=num)
        out = 0.0
        for i, s in enumerate(seq[1:]):
            out += norm(s - seq[i])
        return out


class SymmetricBezier(Bezier):
    def __init__(self, controlpoints=None, mirror=None):
        self._mirror = mirror or Reflection([1.0, 0.0, 0.0])
        super(SymmetricBezier, self).__init__(controlpoints=None)
        if controlpoints:
            self.controlpoints = controlpoints

    # @classmethod
    # def __from_json__(cls, controlpoints, basefactory=None):
    #     sm = cls()
    #     sm.controlpoints = controlpoints
    #     sm.basefactory = basefactory or cls.basefactory
    #     return sm

    @property
    def controlpoints(self):
        return self._data[self.numpoints :]

    @controlpoints.setter
    def controlpoints(self, controlpoints):
        cpts = np.array(controlpoints)
        self.data = np.array(list(self._mirror.apply(cpts)[::-1]) + list(cpts))

    @property
    def numpoints(self):
        return len(self._data) // 2

    @numpoints.setter
    def numpoints(self, num_ctrl, num_points=50):
        if not num_ctrl == self.numpoints:
            data = [self(i) for i in np.linspace(0, 1, num_points)]
            self.fit(np.array(data), num_ctrl)

    @dualmethod
    def fit(cls, data, numpoints=3, start=True, end=True):
        bez = super(SymmetricBezier, cls).fit(
            data, numpoints=2 * numpoints, start=start, end=start
        )
        bez.controlpoints = bez.controlpoints[numpoints:]
        return bez


def choose(n, k):
    if 0 <= k <= n:
        ntok = 1
        ktok = 1
        for t in range(1, min(k, n - k) + 1):
            ntok *= n
            ktok *= t
            n -= 1
        return ntok // ktok
    else:
        return 0
