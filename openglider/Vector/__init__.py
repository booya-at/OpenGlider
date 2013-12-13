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


import numpy as np
from openglider.Utils import sign


def depth(arg):
    if isinstance(arg, list) or isinstance(arg, np.ndarray):
        return max([depth(i) for i in arg]) + 1
    else:
        return 1


def arrtype(arg):
    """return type of a vector list: 2d-point (1), list of 2d-points (2), 3d-point (3), list of 3d-points (4)"""
    ##2d-point//argof2d-points//3d-point//argof3d-points
    ##2d-p: depth 1
    ##equivalent numpy.rank?

    ######Room for improvement here!

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
    return np.sqrt(np.vdot(vector, vector))


def normalize(vector):
    leng = norm(vector)
    if leng > 0:
        return vector / norm(vector)
    raise ValueError("Cannot normalize a vector of length Zero")


def rangefrom(maxl, startpoint=0):
    """Iterative, similar to range() but surrounding a certain startpoint"""
    j = 1
    if 0 <= startpoint <= maxl:
        yield startpoint
    while startpoint-j >= 0 or startpoint+j <= maxl:
        if startpoint+j <= maxl:
            yield startpoint+j
        if maxl >= startpoint-j >= 0:
            yield startpoint-j
        j += 1

def rotation_3d(angle, axis=[1, 0, 0]):
    """3D-Rotation Matrix for (angle[rad],[axis(x,y,z)])"""
    # see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
    a = np.cos(angle / 2)
    (b, c, d) = -normalize(axis) * np.sin(angle / 2)
    return np.array([[a ** 2 + b ** 2 - c ** 2 - d ** 2, 2 * (b * c - a * d), 2 * (b * d + a * c)],
                     [2 * (b * c + a * d), a ** 2 + c ** 2 - b ** 2 - d ** 2, 2 * (c * d - a * b)],
                     [2 * (b * d - a * c), 2 * (c * d + a * b), a ** 2 + d ** 2 - b ** 2 - c ** 2]])

#def Rotation_3D_Wiki(angle,axis=[1,0,0]):
#see http://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle for reference.
#    (x,y,z)=normalize(axis)


def cut(p1, p2, p3, p4):
    """2D-Linear Cut; Returns (pointxy, k, l); Solves the linear system: p1+k*(p2-p1)==p3+l*(p4-p3)"""
    """ |p2x-p1x -(p4x-p3x)|*|k|==|p3x-p1x|"""
    """ |p2y-p1y -(p4y-p3y)|*|l|==|p3y-p1y|"""
    matrix = [[p2[0]-p1[0], p3[0]-p4[0]],
              [p2[1]-p1[1], p3[1]-p4[1]]]
    rhs = [p3[0]-p1[0], p3[1]-p1[1]]
    (k, l) = np.linalg.solve(matrix, rhs)
    return p1 + k*(p2-p1), k, l


class Vectorlist(object):
    def __init__(self, data=[], name="Vector List object"):
        #if arrtype(data) == 2 or arrtype(data) == 4:
        self.data = np.array(data)
        self.name = name

    def __repr__(self):
        return self.data.__str__()

    def __str__(self):
        return self.name

    def __getitem__(self, ik):
        if ik < 0:
            k = ik
            i = 0
        else:
            i = min(int(ik), len(self.data)-2)  # Upper Limit for i
            # case1: 0<ik<len -> k=ik%1;
            # case2: ik>len(self.data) -> k += difference
            k = ik % 1 + max(0, int(ik) - len(self.data)+2)
        return self.data[i] + k * (self.data[i + 1] - self.data[i])

    def __len__(self):
        return len(self.data)

    def copy(self):
        return self.__class__(self.data.copy(), self.name+"_copy")

    # TODO: This can go
    def point(self, i, k=0):
        if i > len(self.data) or i < 0 or not isinstance(i, int):
            raise ValueError("invalid data for listpoint")
        return self.data[i] + k * (self.data[i + 1] - self.data[i])

    def extend(self, start, length):
        if length == 0:
            return start
        direction = sign(length)
        length = abs(length)
        next_value = start - start % 1 + (direction > 0)
        difference = norm(self[start]-self[next_value])
        length -= difference
        #
        while length > 0:
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
            start = next_value
            next_value += direction
            difference = norm(self[next_value]-self[start])
            length -= difference
        # Length is smaller than zero
        length = length
        return next_value + direction * length * abs(next_value-start) / difference

    def extend2(self, start, length):
        direction = sign(length)
        length = abs(length)
        #print("new array:")
        #print("length: %s, start: %s, direction: %s, array length: %s" % (length, start, direction, len(self.data)))
        # TODO: If we should stay in the same cell we increment here:
        next_value = int(start - start % 1 + (direction > 0))
        #length -= difference

        while length > 0:
            #next_value = start + (direction > 0) - start % 1
            #if start % 1:  # start is not an integer yet
            #    next_value = int(start - start % 1 + (direction > 0))
            #else:  # start is an integer
            #    next_value = start + direction
            #print("new passtrough:")
            #clamp it between zero and the last value
            next_value = max(0, min(len(self.data) - 1, next_value))
            #the difference between the start and next_value point
            difference = norm(self[start] - self[next_value])
            print("length: %s, difference: %s, start: %s, next_value: %s" % (length, difference, start, next_value))
            if (next_value == 0 and direction < 0) or (next_value == len(self.data) - 1 and direction > 0):
                # we are on the end of the points, extrapolate the rest
                #return start + direction * (start-next) * length / difference
                # Difference = norm(last-forelast)
                print("break now!, length: %s" % difference)
                break
            length -= difference
            #we may fall out now, set difference right
            difference /= abs(start - next_value)
            start = next_value
            next_value = start + direction
            #print("end of while: %s" % length)
        #print("finished while")
        #print("got difference from: %s and %s" % (next_value, (next_value - direction)))
        #print("start: %s, direction: %s, length: %s, difference: %s" % (start, direction, length, difference))
        return start + direction * length / difference

    def get_length(self, first=0, second=None):
        """Get the (normative) Length of a Part of the Vectorlist"""
        if not second:
            second = len(self)-1
        direction = sign(float(second-first))
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
    def cut(self, p1, p2, startpoint=0):
        for i in rangefrom(len(self)-2, startpoint):
            try:
                thacut = cut(self[i], self[i+1], p1, p2)
            # in case we have parallell lines we dont get a result here, so we continue with i raised...
            except np.linalg.linalg.LinAlgError:
                continue
            if 0 < thacut[1] <= 1.:
                return thacut[0], i+thacut[1]
        # Nothing found yet? check start and end of line
        thacut = []
        # Beginning
        try:
            temp = cut(self[0], self[1], p1, p2)
            if temp[1] < 0:
                thacut.append([temp[0], temp[1], norm(self[0]-self[1])*temp[1]])
        except np.linalg.linalg.LinAlgError:
            pass
        # End
        try:
            i = len(self)-1
            temp = cut(self[i], self[i+1], p1, p2)
            if temp[1] > 0:
                thacut.append([temp[0], i+temp[1], norm(self[i]-self[i+1])*temp[1]])
        except np.linalg.linalg.LinAlgError:
            pass

        if len(thacut) > 0:
            # sort by distance
            thacut.sort(key=lambda x: x[2])
            return thacut[0][0:1]

    def check(self):
        """Check for mistakes in the array, such as for the moment: self-cuttings,"""
        for i in range(len(self.data)-3):
            for j in range(i+1, len(self)-2):
                try:
                    temp = cut(self[i], self[i+1], self[j], self[j+1])
                    if temp[1] <= 1. and temp[2] <= 1.:
                        self.data = np.concatenate([self.data[:i], [temp[0]], self.data[j+1:]])
                except np.linalg.linalg.LinAlgError:
                    continue
                    #if temp[1] == 0.:
                    # TODO: Drop if not a unique point

    def normvectors(self):
        rotate = lambda x: normalize(x).dot([[0, -1], [1, 0]])
        vectors = [rotate(self.data[1]-self.data[0])]
        for j in range(1, len(self.data)-2):
            # TODO: Maybe not normalize here?!
            vectors.append(rotate(normalize(self.data[j+1]-self.data[j])+normalize(self.data[j]-self.data[j-1])))
        vectors.append(rotate(self.data[-1]-self.data[-2]))
        return np.array(vectors)
