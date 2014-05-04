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
import copy

import numpy as np
#from openglider.graphics import graphics, Line  # DEBUG
from openglider.utils import sign
from openglider.utils.cached_property import cached_property


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


def norm(vector):
    """
    Norm-Function for n-dimensional vectors
    """
    return np.sqrt(np.vdot(vector, vector))

def norm_squared(vector):
    """
    Norm_squared
    """
    return np.vdot(vector, vector)


def normalize(vector):
    """
    Normalize n-dimensional vectors
    """
    leng = norm(vector)
    if leng > 0:
        return vector / norm(vector)
    raise ValueError("Cannot normalize a vector of length Zero")


def rangefrom(maxl, startpoint=0):
    """
    yield iterative, similar to range() but surrounding a certain startpoint
    """
    j = 1
    if 0 <= startpoint <= maxl:
        yield startpoint
    while startpoint - j >= 0 or startpoint + j <= maxl:
        if startpoint + j <= maxl:
            yield startpoint + j
        if maxl >= startpoint - j >= 0:
            yield startpoint - j
        j += 1


def rotation_3d(angle, axis=None):
    """
    3D-Rotation Matrix for (angle[rad],[axis(x,y,z)])
    """
    if axis is None:
        axis = [1, 0, 0]
    # see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
    a = np.cos(angle / 2)
    (b, c, d) = -normalize(axis) * np.sin(angle / 2)
    return np.array([[a ** 2 + b ** 2 - c ** 2 - d ** 2, 2 * (b * c - a * d), 2 * (b * d + a * c)],
                     [2 * (b * c + a * d), a ** 2 + c ** 2 - b ** 2 - d ** 2, 2 * (c * d - a * b)],
                     [2 * (b * d - a * c), 2 * (c * d + a * b), a ** 2 + d ** 2 - b ** 2 - c ** 2]])

#def Rotation_3D_Wiki(angle,axis=[1,0,0]):
#see http://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle for reference.
#    (x,y,z)=normalize(axis)


def rotation_2d(angle):
    """
    Return a 2D-Rotation-Matrix
    """
    return np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])


def cut(p1, p2, p3, p4):
    """
    2D-Linear Cut; Solves the linear system: p1+k*(p2-p1)==p3+l*(p4-p3)

    :returns: (point(x, y), k, l)
    """
    """ |p2x-p1x -(p4x-p3x)|*|k|==|p3x-p1x|"""
    """ |p2y-p1y -(p4y-p3y)|*|l|==|p3y-p1y|"""
    matrix = [[p2[0] - p1[0], p3[0] - p4[0]],
              [p2[1] - p1[1], p3[1] - p4[1]]]
    rhs = [p3[0] - p1[0], p3[1] - p1[1]]
    (k, l) = np.linalg.solve(matrix, rhs)
    return p1 + k * (p2 - p1), k, l


class HashedList(object):
    def __init__(self, data=None, name=None):
        self._data = None
        self._hash = None
        self.data = data
        try: # TODO: whats that?
            if name or not self.name:
                raise AttributeError
        except AttributeError:
            self.name = name

    def __getitem__(self, item):
        return self.data.__getitem__(item)

    def __setitem__(self, key, value):
        self.data.__setitem__(key, np.array(value))
        self._hash = None

    def __hash__(self):
        if self._hash is None:
            self._hash = hash(str(self.data))
        return self._hash

    def __len__(self):
        return len(self.data)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        if not data is None:
            self._data = np.array(data)
            #self._data = [np.array(vector) for vector in data]  # 1,5*execution time
            self._hash = None
        else:
            self._data = data

    def copy(self):
        return copy.deepcopy(self)


class Vectorlist(HashedList):
    def __init__(self, data=None, name=None):
        super(Vectorlist, self).__init__(data, name)


    def __repr__(self):
        return self.data.__str__()

    def __str__(self):
        return self.name

    def __getitem__(self, ik):
        if isinstance(ik, int) and 0 <= ik < len(self):  # easiest case
            return self.data[ik]
        elif isinstance(ik, slice):  # example: list[1.2:5.5:1]
            step = 1 if ik.step is None else ik.step
            if step > 0:
                start = max(int(ik.start) + 1, 0)
                stop = min(int(ik.stop) + (1 if ik.stop % 1 > 0 else 0), len(self) - 1)
            else:
                start = min(int(ik.start) - (0 if ik.start % 1 > 0 else 1), len(self) - 1)
                stop = max(int(ik.stop), 0)
            values = [ik.start] + range(start, stop, step) + [ik.stop]
            return [self[i] for i in values]
        else:
            if ik < 0:
                k = ik
                i = 0
            else:
                i = min(int(ik), len(self.data) - 2)  # Upper Limit for i
                # case1: 0<ik<len -> k=ik%1;
                # case2: ik>len(self.data) -> k += difference
                k = ik % 1 + max(0, int(ik) - len(self.data) + 2)
            return self.data[i] + k * (self.data[i + 1] - self.data[i])

    def point(self, x):
        """List.point(x) is the same as List[x]"""
        return self[x]

    def get(self, start, stop):
        start2 = start - start % 1 + 1
        stop2 = stop - stop % 1
        data = self.data[start2:stop2]
        return np.concatenate([[self[start]], data, [self[stop]]])

    def extend(self, start, length):
        if length == 0:
            return start
        direction = sign(length)
        length = abs(length)
        next_value = start - start % 1 + (direction > 0)
        difference = norm(self[start] - self[next_value])
        length -= difference
        #
        while length > 0:
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
            start = next_value
            next_value += direction
            difference = norm(self[next_value] - self[start])
            length -= difference
            # Length is smaller than zero
        length = length
        return next_value + direction * length * abs(next_value - start) / difference

    def get_length(self, first=0, second=None):
        """
        Get the (normative) Length of a Part of the Vectorlist.
        """
        if not second:
            second = len(self) - 1
        direction = sign(float(second - first))
        length = 0
        next_value = int(first - first % 1 + (direction > 0))
        # Just to fasten up
        if next_value > len(self) and direction < 0:
            next_value = len(self)
        elif next_value < 0 < direction:
            next_value = 0
        while next_value * direction < second * direction:
            length += norm(self[next_value] - self[first])
            first = next_value
            next_value += direction
            # Fasten up aswell
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
        return length + norm(self[second] - self[first])


class Vectorlist2D(Vectorlist):
    def __init__(self, data=None, name=None):
        self._normvectors = None
        super(Vectorlist2D, self).__init__(data, name)

    def __add__(self, other):  # this is python default behaviour for lists
        if other.__class__ is self.__class__:
            return self.__class__(np.append(self.data, other.data, axis=0), self.name)
        else:
            raise ValueError("cannot append: ", self.__class__, other.__class__)

    def cut(self, p1, p2, startpoint=0, break_if_found=True,
            cut_only_positive=False, cut_only_in_between=False):
        """
        Cut with two points given, returns (point, position_in_list, k [*(p2-p1)])
        """
        startpoint = int(startpoint)
        cutlist = []

        for i in rangefrom(len(self) - 2, startpoint):
            try:
                thacut = cut(self[i], self[i + 1], p1, p2)  # point, i, k
            except np.linalg.linalg.LinAlgError:
                continue
            if (0 <= thacut[1] < 1 and
                    (not cut_only_positive or thacut[2] >= 0) and
                    (not cut_only_in_between or thacut[2] <= 1.)):
                cutlist.append((thacut[0], i + thacut[1], thacut[2]))
                if break_if_found:
                    return cutlist[0]

        if len(cutlist) > 0:
            return cutlist

        # Nothing found yet? Shit, so, check start and end of line
        # Beginning
        try:
            temp = cut(self[0], self[1], p1, p2)
            if temp[1] <= 0:
                cutlist.append([temp[0], temp[1], norm(self[0] - self[1]) * temp[1]])
        except np.linalg.linalg.LinAlgError:
            pass
        # End
        try:
            i = len(self) - 1
            temp = cut(self[i], self[i + 1], p1, p2)
            if temp[1] > 0:
                cutlist.append([temp[0], i + temp[1], norm(self[i] - self[i + 1]) * temp[1]])
        except np.linalg.linalg.LinAlgError:
            pass

        if len(cutlist) > 0:
            # sort by distance
            cutlist.sort(key=lambda x: x[2])
            #print(cutlist[0])
            return cutlist[0][0:2]
        else:
            #graphics([Line(self.data), Line([p1,p2])])  # DEBUG
            raise ArithmeticError("no cuts discovered for p1:" + str(p1) + " p2:" + str(p2) + str(self[0]) +
                                  str(cut(self[0], self[1], p1, p2)))

    def check(self):  # TODO: IMPROVE (len = len(self.data), len-=,...)
        """
        Check for mistakes in the array, such as for the moment: self-cuttings,..
        """
        for i in range(len(self.data) - 3):
            if i > len(self.data) - 4:
                break
            for j in range(i + 2, len(self.data) - 2):
                if j > len(self.data) - 3:
                    break
                try:
                    temp = cut(self.data[i], self.data[i + 1], self.data[j], self.data[j + 1])
                    if 0 < temp[1] < 1. and 0 < temp[2] < 1.:
                        #self.data = self.data[:i] + [temp[0]] + self.data[j + 1:]
                        self.data = np.concatenate([self.data[:i], [temp[0]], self.data[j+1:]])
                except np.linalg.linalg.LinAlgError:
                    continue

    @cached_property('self')
    def normvectors(self):
        """
        Return Normvectors to the List-Line, heading rhs
        """
        rotate = lambda x: normalize(x).dot([[0, -1], [1, 0]])
        normvectors = [rotate(self.data[1] - self.data[0])]
        for j in range(1, len(self.data) - 1):
            # TODO: Maybe not normalize here?!
            normvectors.append(
                #rotate(normalize(self.data[j + 1] - self.data[j]) + normalize(self.data[j] - self.data[j - 1])))
                rotate(self.data[j + 1] - self.data[j - 1]))
        normvectors.append(rotate(self.data[-1] - self.data[-2]))
        return normvectors


    def shift(self, vector):
        if len(vector) == 2:
            self.data += vector

    def add_stuff(self, amount):
        """
        Shift the whole line for a given amount (->Sewing allowance)
        """
        # cos(vectorangle(a,b)) = (a1 b1+a2 b2)/Sqrt[(a1^2+a2^2) (b1^2+b2^2)]
        newlist = []
        second = self.data[0]
        third = self.data[1]
        newlist.append(second + self.normvectors[0] * amount)
        i = 0
        for i in range(1, len(self.data) - 1):
            first = second
            second = third
            third = self.data[i + 1]
            d1 = third - second
            d2 = second - first
            newlist.append(second + self.normvectors[i] * amount / d1.dot(d2) * np.sqrt(d1.dot(d1) * d2.dot(d2)))
        newlist.append(third + self.normvectors[i + 1] * amount)
        self.data = newlist

    def rotate(self, angle, startpoint=None):
        """
        Rotate around a (non)given startpoint counter-clockwise
        """
        rotation_matrix = rotation_2d(angle)
        new_data = []
        for point in self.data:
            if not startpoint is None:
                new_data.append(startpoint + rotation_matrix.dot(point - startpoint))
            else:
                new_data.append(rotation_matrix.dot(point))
        self.data = new_data


class Polygon2D(Vectorlist2D):
    @property
    def isclosed(self):
        return self.data[0] == self.data[-1]

    def close(self):
        """
        Close the endings of the polygon using a cut.
        """
        try:
            thacut = cut(self.data[0], self.data[1], self.data[-2], self.data[-1])
            if thacut[1] <= 1 and 0 <= thacut[2]:
                self.data[0] = thacut[0]
                self.data[-1] = thacut[0]
                return True
        except ArithmeticError:
            return False

    #TODO: @cached-property
    @property
    def centerpoint(self):
        """
        Return the average point of the polygon.
        """
        return sum(self.data) / len(self.data)

    def contains_point(self, point):
        """
        Check if a Polygon contains a point or not.
        reference: http://en.wikipedia.org/wiki/Point_in_polygon

        :returns: boolean
        """
        # using ray-casting-algorithm
        cuts = self.cut(point, self.centerpoint, break_if_found=False, cut_only_positive=True)
        return bool(len(cuts) % 2)
        # alternative: winding number

