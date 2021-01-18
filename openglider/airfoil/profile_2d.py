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
import os
import re
import math
import numpy as np
import tempfile
import shutil
import logging

from openglider.utils.cache import HashedList
from openglider.utils.distribution import Distribution
from openglider.vector.functions import norm_squared
from openglider.vector.polygon import Polygon2D


logger = logging.getLogger(__name__)

class Profile2D(Polygon2D):
    """
    Profile2D: 2 Dimensional Standard airfoil representative
    """
    def __init__(self, data, name=None):
        self.noseindex = None
        super(Profile2D, self).__init__(data, name)

    def __imul__(self, other):
        fakt = np.array([1, float(other)])
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
        matrix = np.array([[cos_sq, -sin_sq], [sin_sq, cos_sq]])  # de-rotate and scale
        data = np.array([matrix.dot(i - nose) for i in self.data])
        data[-1] = data[0]
        self.data = data
        return self

    @HashedList.data.setter
    def data(self, data):
        HashedList.data.fset(self, data)
        if data is not None:
            i = 0
            while data[i + 1][0] < data[i][0] and i < len(data):
                i += 1
            self.noseindex = i

    def get_data(self, negative_x=False):
        if not negative_x:
            return self.data
        else:
            data = np.array(self.data)
            data[:,0] *= np.array([-1.] * self.noseindex + [1.] * (len(self) - self.noseindex))
            return data

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

    _re_number = r"([-+]?\d*\.\d*(?:[eE][+-]?\d+)?|\d+)"
    _re_coord_line = re.compile(rf"\s*{_re_number}\s+{_re_number}\s*")

    @classmethod
    def import_from_dat(cls, path):
        """
        Import an airfoil from a '.dat' file
        """
        profile = []
        name = 'imported from {}'.format(path)
        with open(path, "r") as p_file:
            for i, line in enumerate(p_file):
                if line.endswith(","):
                    line = line[:-1]

                match = cls._re_coord_line.match(line)

                if match:
                    profile.append([float(i) for i in match.groups()])
                elif i == 0:
                    name = line
                else:
                    logger.error(f"error in dat airfoil: {path} {i}:({line.strip()})")
        return cls(profile, name)

    def export_dat(self, pfad):
        """
        Export airfoil to .dat Format
        """
        with open(pfad, "w") as out:
            if self.name:
                out.write(str(self.name).strip())
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
        x = np.array([i[0] for i in profile])
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
        x = np.array([i[0] for i in profile])
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
        data = [(abs(x), self[self(x)][1]) for x in xval]
        self.data = np.array(data)

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
        return np.array([self.profilepoint(i, 0.) for i in xvals])

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
        # big problem when used with flap
        if hasattr(self, 'data_without_flap'):
            data = self.data_without_flap
        else:
            data = self._data
        for x, y in data:
            if abs(y) > 0.0001:
                return False
        return True

    @property
    def upper_indices(self):
        return range(0, self.noseindex)

    @property
    def lower_indices(self):
        return range(self.noseindex + 1, len(self))

    def insert_point(self, pos, tolerance=1e-5):
        nearest_x_value = self.nearest_x_value(pos)
        if abs(nearest_x_value - pos) < tolerance:
            pass
        else:
            point = self.profilepoint(pos)
            ik = self(pos)
            data = list(self.data)
            data.insert(int(ik + 1), point)
            self.data = data

    def remove_points(self, start, end, tolerance=None):
        new_data = []
        tolerance = 0. or tolerance
        for i, x in enumerate(self.x_values):
            if not (x > (start + tolerance) and x < (end - tolerance)):
                new_data.append(self.data[i])
        self.data = np.array(new_data)

    def move_nearest_point(self, pos):
        ik = self(pos)
        diff = ik % 1.
        if diff < 0.5:
            self.data[int(ik)] = self.profilepoint(pos)
        else:
            self.data[int(ik) + 1] = self.profilepoint(pos)

    def nearest_x_value(self, x):
        min_x_value = None
        min_diff = None
        for i_x in self.x_values:
            diff = abs(x - i_x)
            if not min_x_value or diff < min_diff:
                min_diff = diff
                min_x_value = i_x
        return min_x_value

    def apply_function(self, foo):
        data = np.array(self.data)
        self.data = [foo(i, upper=index < self.noseindex) for index, i in enumerate(data)]

    @classmethod
    def from_url(cls, name='atr72sm', url='http://m-selig.ae.illinois.edu/ads/coord/'):
        import urllib.request
        airfoil_name = name + '.dat'
        temp_name = os.path.join(tempfile.gettempdir(), airfoil_name)
        with urllib.request.urlopen(url + airfoil_name) as data_file, open(temp_name, 'w') as dat_file:
            dat_file.write(data_file.read().decode('utf8'))
        data = np.loadtxt(temp_name, usecols=(0, 1), skiprows=1)
        if data[0, 0] > 1.5:
            data = data[1:]
        return cls(data, name)

    def set_flap(self, flap_begin, flap_amount):
        @np.vectorize
        def f(x, a, b):
            c1, c2, c3 = -a**2*b/(a**2 - 2*a + 1), 2*a*b/(a**2 - 2*a + 1), -b/(a**2 - 2*a + 1)
            if x < a:
                return 0.
            if x > 1:
                return -b
            return c1 + c2 * x + c3 * x**2
        x, y = self.data.T
        dy = f(x, flap_begin, flap_amount)
        if not hasattr(self, 'data_without_flap'):
            self.data_without_flap = self.data
        self.data = np.array([x, y + dy]).T


    def calc_drag(self, re=2e6, cl=0.7):
        if not shutil.which('xfoil'):
            logger.error("xfoil is not available")
            return None
        from openglider.airfoil.XFoilCalc import calc_drag
        return calc_drag(self, re, cl)