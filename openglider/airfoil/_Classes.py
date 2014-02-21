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
# TODO: Migrate ALL to __init__
import math
import os  # for xfoil execution
import numpy  # array spec

#from openglider.airfoil._XFoilCalc import XValues, Calcfile, Impresults
from openglider.vector import normalize, norm, Vectorlist2D, Vectorlist, Polygon2D


def get_x_value(x_value_list, x):
    """
    Get position of x in a list of x_values
    zb get_x_value([1,2,3],1.5)=0.5
    """
    for i in range(len(x_value_list) - 1):
        if x_value_list[i + 1] >= x or i == len(x_value_list) - 2:
            return i - (x_value_list[i] - x) / (x_value_list[i + 1] - x_value_list[i])


class BasicProfile2D(Polygon2D):
    """Basic airfoil Class, not to do much, but just"""
    ####rootprof gleich mitspeichern!!
    def __init__(self, profile=None, name=None):
        self.noseindex = None
        super(BasicProfile2D, self).__init__(profile, name)

    def __mul__(self, other):
        fakt = numpy.array([1, float(other)])
        return self.__class__(self.data * fakt)

    def __call__(self, xval):
        return self.profilepoint(xval)

    #def align(self, (x, y)):
    #    """Align a point (x, y) on the airfoil. x (0,1); y (-1,1)"""
    #    pass
    def _x(self, xval):
        pass  # Maybe split up profilepoint function

    def profilepoint(self, xval, h=-1.):
        """Get airfoil Point for x-value (<0:upper side) optional: height (-1:lower,1:upper), possibly mapped"""
        if not h == -1:  # middlepoint
            p1 = self.profilepoint(xval)[1]
            p2 = self.profilepoint(-xval)[1]
            return p1 + (1. + h) / 2 * (p2 - p1)
        else:  # Main Routine
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
            return i + k, self[i + k]

    def normalize(self):
        """
        Normalize the airfoil.
        This routine does:
            *Put the nose back to (0,0)
            *De-rotate airfoil
            *Reset its length to 1
        """
        #to normalize do: put nose to (0,0), rotate to fit (1,0), normalize to (1,0)
        p1 = self.data[0]
        dmax = 0.
        nose = p1
        for i in self.data:
            temp = norm(i - p1)
            if temp > dmax:
                dmax = temp
                nose = i

        diff = p1 - nose
        sin = diff.dot([0, -1]) / dmax  # Angle: a.b=|a|*|b|*sin(alpha)
        cos = numpy.sqrt(1 - sin ** 2)
        matrix = numpy.array([[cos, -sin], [sin, cos]]) / dmax  # de-rotate and scale
        self.data = numpy.array([matrix.dot(i - nose) for i in self.data])

    @Vectorlist.data.setter
    def data(self, data):
        Vectorlist2D.data.fset(self, data)
        if not data is None:
            i = 0
            while data[i + 1][0] < data[i][0] and i < len(data):
                i += 1
            self.noseindex = i


class Profile2D(BasicProfile2D):
    """Profile2D: 2 Dimensional Standard airfoil representative in OpenGlider"""
    #############Initialisation###################
    def __init__(self, profile=None, name=None, normalize_root=True):
        if not profile is None and len(profile) > 2:
            # Filter name
            if isinstance(profile[0][0], str):
                name = profile[0][0]
                profile = profile[1:]
        self._rootprof = BasicProfile2D(profile, name)  # keep a copy
        super(Profile2D, self).__init__(profile, name=name)
        if normalize_root and profile is not None:
            self._rootprof.normalize()
            self.reset()

    def __add__(self, other, conservative=False):
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

    def __eq__(self, other):
        return numpy.allclose(self.data, other.data)

    def importdat(self, path):
        """
        Import a *.dat airfoil (a tab seperated list of x/y - values
        """
        if not os.path.isfile(path):
            raise Exception("airfoil not found in" + path + "!")
        profile = []
        name = None
        with open(path, "r") as pfile:
            for line in pfile:
                #line = line.strip()
                ###tab-seperated values except first line->name
                if "\t" in line or " " in line:
                    line = line.split()
                    if len(line) == 2:
                        profile.append([float(i) for i in line])
                else:
                    name = line.strip()
            self.__init__(profile, name)

    def export(self, pfad):
        """
        Export airfoil in .dat Format
        """
        with open(pfad, "w") as out:
            if self.name:
                out.write(str(self.name))
            for i in self.data:
                out.write("\n" + str(i[0]) + "\t" + str(i[1]))
        return pfad

    def rootpoint(self, xval, h=-1):
        """Get airfoil Point for x-value (<0:upper side) optional: height (-1:lower,1:upper);
        use root-airfoil (highest res)"""
        return self._rootprof.profilepoint(xval, h)

    def reset(self):
        """Reset airfoil To Root-Values"""
        self.data = self._rootprof.data

    def area(self):
        """Return the area occupied by the airfoil"""
        area = 0
        last = self.data[0]
        for this in self.data[1:]:
            diff = this - last
            area += abs(diff[0] * last[1] + 0.5 * diff[0] * diff[1])
        return area

    def compute_naca(self, naca=1234, numpoints=None):
        """Compute a four-digit naca-airfoil"""
        # See: http://people.clarkson.edu/~pmarzocc/AE429/The%20NACA%20airfoil%20series.pdf
        # and: http://airfoiltools.com/airfoil/naca4digit
        m = int(naca / 1000) * 0.01  # Maximum Camber Position
        p = int((naca % 1000) / 100) * 0.1  # second digit: Maximum Thickness position
        t = (naca % 100) * 0.01  # last two digits: Maximum Thickness(%)
        if numpoints is None:
            numpoints = self.numpoints  # if here is an error, you should give a numpoints argument
        x_values = [math.cos(x * 1. / (numpoints - 1) * math.pi / 2) for x in range(1, numpoints)]

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
        self.__init__(upper + lower[1:][::-1], name="NACA_" + str(naca))

    #todo: cached??
    @property
    def x_values(self):
        """Get XValues of airfoil. upper side neg, lower positive"""
        i = self.noseindex
        return numpy.concatenate((self.data[:i, 0] * -1., self.data[i:, 0]))

    @x_values.setter
    def x_values(self, xval):
        """Set X-Values of airfoil to defined points."""
        ###standard-value: root-prof xvalues
        self.data = [self._rootprof(x)[1] for x in xval]

    @property
    def numpoints(self):
        return len(self.data)

    @numpoints.setter
    def numpoints(self, num):
        """Set airfoil to cosinus-Distributed XValues"""
        i = num - num % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 - math.sin(math.pi * x))
        self.x_values = [xtemp(j * 1. / i) for j in range(i + 1)]

    #todo: cached
    @property
    def thickness(self):
        """with no arg the max thick is returned"""
        xvals = sorted(set(map(abs, self.x_values)))
        return max([self.profilepoint(-i)[1][1] - self.profilepoint(i)[1][1] for i in xvals])

    @thickness.setter
    def thickness(self, newthick):
        factor = float(newthick / self.thickness)
        new = self.data * [1., factor]
        name = self.name
        if not name is None:
            name += "_" + str(newthick) + "%"
        self.__init__(new, name)

    @property
    def camber(self, *xvals):
        """return the camber of the airfoil for certain x-values or if nothing supplied, camber-line"""
        if not xvals:
            xvals = sorted(set(map(abs, self.x_values)))
        return numpy.array([self.profilepoint(i, 0.) for i in xvals])

    @camber.setter
    def camber(self, newcamber):
        """Set maximal camber to the new value"""
        now = self.camber
        factor = newcamber / max(now[:, 1]) - 1
        now = dict(now)
        self.__init__([i + [0, now[i[0]] * factor] for i in self.data])


# TODO: PYXFOIL INTEGRATION INSTEAD OF THIS or xflr5-python?
class XFoil(Profile2D):
    """XFoil Calculation airfoil based on Profile2D"""

    def __init__(self, profile=None):
        Profile2D.__init__(self, profile)
        self._xvalues = self.x_values
        self._calcvalues = []

    def _change(self):
        """Check if something changed in coordinates"""
        checkval = self._xvalues == self.x_values
        if not isinstance(checkval, bool):
            checkval = checkval.all()
        return checkval

    def _calc(self, angles):

        resfile = "/tmp/result.dat"
        pfile = "/tmp/calc_pfile.dat"
        #cfile = Calcfile(angles, resfile)

        self.export(pfile)
        #status = os.system("xfoil " + pfile + " <" + cfile + " > /tmp/log.dat")
        #if status == 0:
        #    result = Impresults(resfile)
        #    for i in result:
        #        self._calcvalues[i] = result[i]
        #    os.system("rm " + resfile)
        #os.system("rm " + pfile + " " + cfile)
        #return True

    def _get(self, angle, exact=1):
        if self._change():
            self._calcvalues = {}
            self._xvalues = self.x_values[:]
        print(self._calcvalues)
        #calcangles = XValues(angle, self._calcvalues)
        #print("ho!" + str(calcangles))
        #if len(calcangles) > 0:
        #    erg = self._calc(calcangles)
        #    print("soso")
        #    return erg
        ##self._calcvalues=[1,2]


class Profile3D(Vectorlist):
    def __init__(self, profile=None, name="Profile3d"):
        super(Profile3D, self).__init__(profile, name)
        self._normvectors = self._tangents = None
        self._diff = self._xvekt = self._yvekt = None
        self.xvect = self.yvect = None

    def projection(self):
        if not self._xvekt or not self._yvekt or not self._diff:
            p1 = self.data[0]
            diff_len = nose_index = 0
            diff = [p - p1 for p in self.data]
            for i in range(len(self.data)):
                thisdiff = norm(diff[i])
                if thisdiff > diff_len:
                    nose_index = i
                    diff_len = thisdiff

            xvect = normalize(diff[nose_index])
            yvect = numpy.array([0, 0, 0])

            for i in range(len(diff)):
                sign = 1 - 2 * (i > nose_index)
                yvect = yvect + sign * (diff[i] - xvect * xvect.dot(diff[i]))

            self.xvect = xvect
            self.yvect = normalize(yvect)
            self._diff = diff
            self.noseindex = nose_index

    def flatten(self):
        """Flatten the airfoil and return a 2d-Representative"""
        self.projection()
        return Profile2D([[-self.xvect.dot(i), self.yvect.dot(i)] for i in self._diff], name=self.name + "_flattened")
        ###find x-y projection-layer first

    def normvectors(self):
        if not self._normvectors:
            self.projection()
            profnorm = numpy.cross(self.xvect, self.yvect)
            func = lambda x: normalize(numpy.cross(x, profnorm))
            vectors = [func(self.data[1] - self.data[0])]
            for i in range(1, len(self.data) - 1):
                vectors.append(func(
                    normalize(self.data[i + 1] - self.data[i]) +
                    normalize(self.data[i] - self.data[i - 1])))
            vectors.append(func(self.data[-1] - self.data[-2]))
            self._normvectors = vectors
        return self._normvectors

    def tangents(self):
        if not self._tangents:
            second = self.data[0]
            third = self.data[1]
            self._tangents = [normalize(third - second)]
            for element in self.data[2:]:
                first = second
                second = third
                third = element
                self._tangents.append(normalize(normalize(third - second) + normalize(second - first)))
            self._tangents.append(normalize(third - second))
        return self._tangents



