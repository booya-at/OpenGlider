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
import os
import math
import numpy
import tempfile
import urllib.request
import shutil

from openglider.utils.cache import HashedList
from openglider.utils.distribution import Distribution
from openglider.vector.functions import norm_squared
from openglider.vector.polygon import Polygon2D


class Profile2D(Polygon2D):
    """
    Profile2D: 2 Dimensional Standard airfoil representative
    """
    def __init__(self, data, name=None):
        self.noseindex = None
        super(Profile2D, self).__init__(data, name)

    def __imul__(self, other):
        fakt = numpy.array([1, float(other)])
        return super(Profile2D, self).__imul__(fakt)

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

    def profilepoint(self, xval, h=-1.):
        """
        Get airfoil Point for x-value (<0:upper side)
        optional: height (-1:lower,1:upper)
        """
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
        return self

    @HashedList.data.setter
    def data(self, data):
        HashedList.data.fset(self, data)
        if data is not None:
            i = 0
            while data[i + 1][0] < data[i][0] and i < len(data):
                i += 1
            self.noseindex = i

    def __add__(self, other, conservative=False):
        """
        Mix 2 Profiles
        """
        first = self.copy()
        first += other
        return first

    def __iadd__(self, other):
        for i, point in enumerate(self.data):
            if i > self.noseindex:
                x = point[0]
            else:
                x = -point[0]

            point[1] += other[other(x)][1]
        return self

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

    def export_dat(self, pfad):
        """
        Export airfoil to .dat Format
        """
        with open(pfad, "w") as out:
            if self.name:
                out.write(str(self.name))
            for p in self.data:
                out.write("\n{:.12f}\t{:.12}".format(*p))
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

    @classmethod
    def compute_joukowsky(cls, m=-0.1+0.1j, numpoints=100):
        from openglider.airfoil.conformal_mapping import JoukowskyAirfoil
        airfoil = JoukowskyAirfoil(m)
        profile = [[c.real, c.imag] for c in airfoil.coordinates(numpoints)]

        # find the smallest xvalue to reset the nose
        x = numpy.array([i[0] for i in profile])
        profile = cls(profile, "joukowsky_" + str(m))
        profile.normalize()
        profile.numpoints = numpoints
        return profile

    @classmethod
    def compute_vandevooren(cls, tau=0.05, epsilon=0.05, numpoints=100):
        from openglider.airfoil.conformal_mapping import VanDeVoorenAirfoil
        airfoil = VanDeVoorenAirfoil(tau=tau, epsilon=epsilon)
        profile = [[c.real, c.imag] for c in airfoil.coordinates(numpoints)]

        # find the smallest xvalue to reset the nose
        profile = cls(profile, "VanDeVooren_tau=" + str(tau) + "_epsilon=" + str(epsilon))
        profile.normalize()
        profile.numpoints = numpoints
        return profile

    @classmethod
    def compute_trefftz(cls, m=-0.1+0.1j, tau=0.05, numpoints=100):
        from openglider.airfoil.conformal_mapping import TrefftzKuttaAirfoil
        airfoil = TrefftzKuttaAirfoil(midpoint=m, tau=tau)
        profile = [[c.real, c.imag] for c in airfoil.coordinates(numpoints)]

        # find the smallest xvalue to reset the nose
        x = numpy.array([i[0] for i in profile])
        profile = cls(profile, "TrefftzKuttaAirfoil_m=" + str(m) + "_tau=" + str(tau))
        profile.normalize()
        profile.numpoints = numpoints
        return profile

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
        self.data = [self[self(x)] for x in xval]

    @property
    def numpoints(self):
        return len(self.data)

    @numpoints.setter
    def numpoints(self, numpoints):
        self.x_values = Distribution.from_cos_distribution(numpoints)

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
    def camber(self):
        """return the maximum camber of the airfoil"""
        return max([p[1] for p in self.camber_line])

    @camber.setter
    def camber(self, newcamber):
        """Set maximal camber to the new value"""
        old_camber = self.camber
        factor = newcamber / old_camber - 1
        now = dict(self.camber_line)
        self.data = [i + [0, now[i[0]] * factor] for i in self.data]

    @property
    def has_zero_thickness(self):
        for x, y in self._data:
            if abs(y) > 0.0001:
                return False
        return True

    @property
    def upper_indices(self):
        return range(0, self.noseindex)

    @property
    def lower_indices(self):
        return range(self.noseindex + 1, len(self))

    def insert_point(self, pos):
        if pos in self.x_values:
            pass
        else:
            point = self.profilepoint(pos)
            ik = self(pos)
            data = list(self.data)
            data.insert(int(ik + 1), point)
            self.data = data

    def apply_function(self, foo):
        data = numpy.array(self.data)
        self.data = [foo(i, upper=index < self.noseindex) for index, i in enumerate(data)]

    @classmethod
    def from_url(cls, name='atr72sm', url='http://m-selig.ae.illinois.edu/ads/coord/'):
        airfoil_name = name + '.dat'
        temp_name = os.path.join(tempfile.gettempdir(), airfoil_name)
        with urllib.request.urlopen(url + airfoil_name) as data_file, open(temp_name, 'w') as dat_file:
            dat_file.write(data_file.read().decode('utf8'))
        data = numpy.loadtxt(temp_name, usecols=(0, 1), skiprows=1)
        return cls(data, name)

    def calc_drag(self, re=200000, cl=0.7):
        if not shutil.which('xfoil'):
            print('command xfoil is not available')
            return None
        from openglider.airfoil.XFoilCalc import calc_drag
        return calc_drag(self, re, cl)