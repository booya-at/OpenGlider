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

from openglider.vector.functions import norm, norm_squared, normalize
from openglider.vector.polyline import PolyLine, PolyLine2D
from openglider.vector.polygon import Polygon2D

def depth(arg):
    try:
        return max([depth(i) for i in arg]) + 1
    except TypeError:  # Not a list anymore
        return 1


def arrtype(arg):
    """
    return type of a vector list: 2d-point (1), list of 2d-points (2), 3d-point (3), list of 3d-points (4)
    """
    ##2d-point//argof2d-points//3d-point//argof3d-points
    ##2d-p: depth 1
    ##equivalent numpy.rank?

    # TODO: Room for improvement here!
    # todo: remove!

    if depth(arg) == 2:
        if len(arg) == 2:
            return 1
        elif len(arg) == 3:
            return 3
        else:
            return 0
    elif depth(arg) == 3:
        if [depth(i) for i in arg] == [2 for i in arg]:
            if [len(i) for i in arg] == [2 for i in arg]:
                return 2
            elif [len(i) for i in arg] == [3 for i in arg]:
                return 4
            else:
                return 0
        else:
            return 0
    else:
        return 0


def mirror_func(direction=None):
    if direction is None:
        direction = [1., 0., 0.]
    if len(direction) == 2:
        x, y = normalize(direction)
        mirrormat=numpy.array(
            [
                [1 - 2 * x ** 2, -2 * x * y],
                [-2 * x * y, 1 - 2 * y ** 2]
            ]
        )
    else:
        x, y, z = normalize(direction)
        mirrormat = numpy.array(
            [
                [1 - 2 * x ** 2, -2 * x * y, -2 * x * z],
                [-2 * x * y, 1 - 2 * y ** 2, -2 * y * z],
                [-2 * x * z, -2 * y * z, 1 - 2 * z ** 2]
            ]
        )

    def mirror(vec):
        if len(vec) == 2 and not isinstance(vec[0], (numpy.ndarray, list, tuple)):
            return numpy.dot(vec, mirrormat).tolist()
        else:
            return numpy.array([mirror(i) for i in vec]).tolist()

    return mirror

mirror2D_x = mirror_func(direction=[1., 0.])
mirror_x = mirror_func(direction=[1., 0., 0.])


class Layer(object):
    def __init__(self, p0, v1, v2):
        self.p0 = numpy.array(p0)
        self.v1 = numpy.array(v1)
        self.v2 = numpy.array(v2)

    def point(self, x1, x2):
        return self.p0 + x1 * self.v1 + x2 * self.v2

    def cut(self, p1, p2):
        """
        cut two points
        eq: p1 + x1*(p2-p1) = self.p0 + x2 * self.v1 + x3*self.r2
        - x1*(p2-p1) + x2 * self.v1 + x3 * self.v2 = p1 - self.p0
        """
        lhs = numpy.matrix([p1-p2, self.v1, self.v2]).transpose()
        rhs = p1 - self.p0
        res = numpy.linalg.solve(lhs, rhs)
        print("res: ", res, lhs, rhs)
        return res[0], res[1:], self.point(res[1], res[2])

    def projection(self, point):
        diff = point - self.p0
        return [self.v1.dot(diff), self.v2.dot(diff)]

    @property
    def translation_matrix(self):
        return numpy.matrix(self.v1, self.v2, self.normvector).transpose()

    def align(self, point_3d):
        return self.p0 + self.translation_matrix.dot(point_3d)

    def normalize(self):
        self.v1 = normalize(self.v1)
        self.v2 = normalize(self.v2 - self.v1 * self.v1.dot(self.v2))

    @property
    def normvector(self):
        return numpy.cross(self.v1, self.v2)

    @normvector.setter
    def normvector(self, normvector):
        #assert isinstance(normvector, np.ndarray)
        # todo: fix // write test
        self.v1 = numpy.array([1,1,1])
        self.v1 = self.v1 - self.v1 * normvector
        #self.v1 = numpy.array([0, -normvector[3], normvector[2]])
        self.v2 = numpy.cross(self.v1, normvector)

