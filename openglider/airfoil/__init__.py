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
import math
import os
import numpy

from openglider.utils.cache import cached_property, HashedList
from openglider.vector import Layer
from openglider.vector.functions import norm, norm_squared, normalize
from openglider.vector.polygon import Polygon2D
from openglider.vector.polyline import PolyLine, PolyLine2D


def get_x_value(x_value_list, x):
    """
    Get position of x in a list of x_values
    zb get_x_value([1,2,3],1.5)=0.5
    """
    for i in range(len(x_value_list) - 1):
        if x_value_list[i + 1] >= x or i == len(x_value_list) - 2:
            return i - (x_value_list[i] - x) / (x_value_list[i + 1] - x_value_list[i])


class BasicProfile2D(Polygon2D):
    """Basic airfoil Class, not to do much"""
    def __init__(self, data, name=None):
        self.noseindex = None
        super(BasicProfile2D, self).__init__(data, name)

    def __imul__(self, other):
        fakt = numpy.array([1, float(other)])
        return super(BasicProfile2D, self).__imul__(fakt)

    def __call__(self, xval):
        xval = float(xval)
        if xval < 0.:       # LOWER
            i = 1
            xval = -xval
            while self[i][0] >= xval and i < len(self):
                i += 1
            i -= 1
        elif xval == 0:     # NOSE
            i = self.noseindex - 1
        else:               # UPPER
            i = len(self) - 2
            while self[i][0] > xval and i > 1:
                i -= 1
                # Determine k-value
        k = -(self[i][0] - xval) / (self[i + 1][0] - self[i][0])

        return i + k

    def align(self, p):
        """Align a point (x, y) on the airfoil. x: (0,1), y: (-1,1)"""
        x, y = p
        upper = self[self(-x)]
        lower = self[self(x)]

        return lower + (upper-lower) * (y + 1)/2

    @staticmethod
    def cos_distribution(numpoints):
        """return cosinus distributed x-values"""
        numpoints -= numpoints % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 - math.sin(math.pi * x))
        return [xtemp(i/numpoints) for i in range(numpoints+1)]

    @staticmethod
    def cos_2_distribution(numpoints):
        """return cosinus distributed x-values"""
        numpoints -= numpoints % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 + math.cos(2 * math.pi * x)) / 2
        return [xtemp(i/numpoints) for i in range(numpoints+1)]

    def profilepoint(self, xval, h=-1.):
        """Get airfoil Point for x-value (<0:upper side) optional: height (-1:lower,1:upper), possibly mapped"""
        if not h == -1:  # middlepoint
            p1 = self[self(xval)]
            p2 = self[self(-xval)]
            return p1 + (1. + h) / 2 * (p2 - p1)
        else:  # Main Routine
            return self[self(xval)]

    def normalize(self):
        """
        Normalize the airfoil.
        This routine does:
            *Put the nose back to (0,0)
            *De-rotate airfoil
            *Reset its length to 1
        """
        p1 = self.data[0]

        nose = self.data[self.noseindex]
        diff = p1 - nose  # put nose to (0,0)
        sin_sq = diff.dot([0, -1]) / norm_squared(diff)  # Angle: a.b=|a|*|b|*sin(alpha)
        cos_sq = diff.dot([1, 0]) / norm_squared(diff)
        matrix = numpy.array([[cos_sq, -sin_sq], [sin_sq, cos_sq]])  # de-rotate and scale
        self.data = numpy.array([matrix.dot(i - nose) for i in self.data])

    @HashedList.data.setter
    def data(self, data):
        HashedList.data.fset(self, data)
        if data is not None:
            i = 0
            while data[i + 1][0] < data[i][0] and i < len(data):
                i += 1
            self.noseindex = i


class Profile2D(BasicProfile2D):
    """
    Profile2D: 2 Dimensional Standard airfoil representative
    """
    def __init__(self, data, name=None, normalize_root=True):
        self._rootprof = BasicProfile2D(data, name)  # keep a copy
        super(Profile2D, self).__init__(data, name=name)
        if normalize_root and data is not None:
            self._rootprof.normalize()
            self.reset()

    def __json__(self):
        return {'rootprof': self._rootprof,
                'data': self.data,
                'name': self.name}

    @classmethod
    def __from_json__(cls, rootprof, data, name):
        profile = cls(data, name)
        profile._rootprof = rootprof
        return profile

    def __add__(self, other, conservative=False):
        """
        Mix 2 Profiles
        """
        # TODO: set rootprof aswell
        if other.__class__ == self.__class__:
            #use the one with more points
            if self.numpoints > other.numpoints or conservative:
                # Conservative means to always use this profiles xvalue
                # (new = this + other)
                first = other.copy()
                second = self
            else:
                first = self.copy()
                second = other

            if not numpy.array_equal(first.x_values, second.x_values):
                first.x_values = second.x_values
            first.data = first.data + second.data * numpy.array([0, 1])
            return first

    def __imul__(self, other):
        self._rootprof *= other
        return super(Profile2D, self).__imul__(other)

    def __eq__(self, other):
        return numpy.allclose(self.data, other.data)

    @classmethod
    def import_from_dat(cls, path):
        """
        Import an airfoil from a '.dat' file
        """
        profile = []
        name = 'imported from {}'.format(path)
        with open(path, "r") as p_file:
            for line in p_file:
                split_line = line.split()
                if len(split_line) == 2:
                    profile.append([float(i) for i in split_line])
                else:
                    name = line
        return cls(profile, name)

    def export(self, pfad):
        """
        Export airfoil to .dat Format
        """
        with open(pfad, "w") as out:
            if self.name:
                out.write(str(self.name))
            for i in self.data:
                out.write("\n" + str(i[0]) + "\t" + str(i[1]))
        return pfad

    @classmethod
    def compute_naca(cls, naca=1234, numpoints=100):
        """Compute and return a four-digit naca-airfoil"""
        # See: http://people.clarkson.edu/~pmarzocc/AE429/The%20NACA%20airfoil%20series.pdf
        # and: http://airfoiltools.com/airfoil/naca4digit
        m = int(naca / 1000) * 0.01  # Maximum Camber Position
        p = int((naca % 1000) / 100) * 0.1  # second digit: Maximum Thickness position
        t = (naca % 100) * 0.01  # last two digits: Maximum Thickness(%)
        x_values = [1-math.sin((x * 1. / (numpoints-1)) * math.pi / 2) for x in range(numpoints)]
        #x_values = self.cos_distribution(numpoints)

        upper = []
        lower = []
        a0 = 0.2969
        a1 = -0.126
        a2 = -0.3516
        a3 = 0.2843
        a4 = -0.1015

        for x in x_values:
            if x < p:
                mean_camber = (m / (p ** 2) * (2 * p * x - x ** 2))
                gradient = 2 * m / (p ** 2) * (p - x)
            else:
                mean_camber = (m / ((1 - p) ** 2) * ((1 - 2 * p) + 2 * p * x - x ** 2))
                gradient = 2 * m / (1 - p ** 2) * (p - x)

            thickness_this = t / 0.2 * (a0 * math.sqrt(x) + a1 * x + a2 * x ** 2 + a3 * x ** 3 + a4 * x ** 4)
            #theta = math.atan(gradient)
            costheta = (1 + gradient ** 2) ** (-0.5)
            sintheta = gradient * costheta
            upper.append([x - thickness_this * sintheta,
                          mean_camber + thickness_this * costheta])
            lower.append([x + thickness_this * sintheta,
                          mean_camber - thickness_this * costheta])
        return cls(upper + lower[::-1][1:], name="NACA_" + str(naca))

    def reset(self):
        """Reset airfoil To Root-Values"""
        self.data = self._rootprof.data

    #@cached_property('self')
    @property
    def x_values(self):
        """Get XValues of airfoil. upper side neg, lower positive"""
        i = self.noseindex
        return [-vector[0] for vector in self.data[:i]] + \
               [vector[0] for vector in self.data[i:]]

    @x_values.setter
    def x_values(self, xval):
        """Set X-Values of airfoil to defined points."""
        ###standard-value: root-prof xvalues
        self.data = [self._rootprof[self._rootprof(x)] for x in xval]

    @property
    def numpoints(self):
        return len(self.data)

    @numpoints.setter
    def numpoints(self, num):
        """Set airfoil to cosinus-Distributed XValues"""
        self.x_values = self.cos_distribution(num)

    #todo: cached
    #@cached_property('self')
    @property
    def thickness(self):
        """return the maximum sickness (Sic!) of an airfoil"""
        xvals = sorted(set(map(abs, self.x_values)))
        return max([self[self(-i)][1] - self[self(i)][1] for i in xvals])

    @thickness.setter
    def thickness(self, newthick):
        factor = float(newthick / self.thickness)
        new = [point * [1., factor] for point in self.data]
        name = self.name
        if name is not None:
            name += "_" + str(newthick) + "%"
        self.__init__(new, name)

    @property
    def camber_line(self):
        xvals = sorted(set(map(abs, self.x_values)))
        return numpy.array([self.profilepoint(i, 0.) for i in xvals])

    #@cached_property('self')
    @property
    def camber(self, *xvals):
        """return the maximum camber of the airfoil"""
        return max([p[1] for p in self.camber_line])

    @camber.setter
    def camber(self, newcamber):
        """Set maximal camber to the new value"""
        old_camber = self.camber
        factor = newcamber / old_camber - 1
        now = dict(self.camber_line)
        self.__init__([i + [0, now[i[0]] * factor] for i in self.data])


class Profile3D(PolyLine):
    @cached_property('self')
    def noseindex(self):
        p0 = self.data[0]
        max_dist = 0
        noseindex = 0
        for i, p1 in enumerate(self.data):
            diff = norm(p1 - p0)
            if diff > max_dist:
                noseindex = i
                max_dist = diff
        return noseindex

    @cached_property('self')
    def projection_layer(self):
        """
        Projection Layer of profile_3d
        """
        p1 = self.data[0]
        diff = [p - p1 for p in self.data]

        xvect = normalize(-diff[self.noseindex])
        yvect = numpy.array([0, 0, 0])

        for i in range(len(diff)):
            sign = 1 - 2 * (i > self.noseindex)
            yvect = yvect + sign * (diff[i] - xvect * xvect.dot(diff[i]))

        yvect = normalize(yvect)
        return Layer(self.data[self.noseindex], xvect, yvect)

    def flatten(self):
        """Flatten the airfoil and return a 2d-Representative"""
        layer = self.projection_layer
        return Profile2D([layer.projection(p) for p in self.data],
                         name=self.name or '' + "_flattened")

    @cached_property('self')
    def normvectors(self):
        layer = self.projection_layer
        profnorm = layer.normvector
        get_normvector = lambda x: normalize(numpy.cross(x, profnorm))

        vectors = [get_normvector(self.data[1] - self.data[0])]
        for i in range(1, len(self.data) - 1):
            vectors.append(get_normvector(
                normalize(self.data[i + 1] - self.data[i]) +
                normalize(self.data[i] - self.data[i - 1])))
        vectors.append(get_normvector(self.data[-1] - self.data[-2]))

        return vectors

    @property
    def tangents(self):
        second = self.data[0]
        third = self.data[1]
        tangents = [normalize(third - second)]
        for element in self.data[2:]:
            first = second
            second = third
            third = element
            tangent = numpy.array([0, 0, 0])
            for vec in [third-second, second-first]:
                try:
                    tangent = tangent + normalize(vec)
                except ValueError:  # zero-length vector
                    pass
            tangents.append(tangent)
        tangents.append(normalize(third - second))
        return tangents




