# TODO: Migrate ALL to __init__


import math
import os  # for xfoil execution

import numpy  # array spec
from ._XFoilCalc import XValues, Calcfile, Impresults
from ..Vector import normalize, norm, Vectorlist2D, Vectorlist


class BasicProfile2D(Vectorlist2D):
    """Basic Profile Class, not to do much, but just"""
    ####rootprof gleich mitspeichern!!
    def __init__(self, profile, name="basicprofile"):
        self._setprofile(profile)
        self.name = name

    def __mul__(self, other):
        fakt = numpy.array([1, float(other)])
        return self.__class__(self.Profile * fakt)

    def __call__(self, xval):
        return self.profilepoint(xval)

    def profilepoint(self, xval, h=-1):
        """Get Profile Point for x-value (<0:upper side) optional: height (-1:lower,1:upper), possibly mapped"""
        if h == -1:  # Main Routine
            xval = float(xval)
            if xval < 0.:       # LOWER
                i = 1
                xval = -xval
                while self[i][0] >= xval and i < len(self):
                    i += 1
                i -= 1
            elif xval == 0:     # NOSE
                i = self.noseindex-1
            else:               # UPPER
                i = len(self) - 2
                while self[i][0] > xval and i > 1:
                    i -= 1
            # Determine k-value
            k = -(self[i][0] - xval) / (self[i + 1][0] - self[i][0])
            return i+k, self[i+k]
        else:   # middlepoint
            p1 = self.profilepoint(xval)[1]
            p2 = self.profilepoint(-xval)[1]
            return p1 + h*(p2-p1)

    # TODO: Get rid of this
    def points(self, xvalues):
        """Map a list of XValues onto the Profile"""
        return numpy.array([self.profilepoint(x) for x in xvalues])

    def normalize(self):
        p1 = self.data[0]
        dmax = 0.
        nose = p1
        for i in self.data:
            temp = norm(i - p1)
            if temp > dmax:
                dmax = temp
                nose = i
            #to normalize do: put nose to (0,0), rotate to fit (1,0), normalize to (1,0)
        #use: a.b=|a|*|b|*cos(alpha)->
        diff = p1 - nose
        sin = diff.dot([0, -1]) / dmax  # equal to cross product of (x1,y1,0),(x2,y2,0)
        cos = numpy.sqrt(1 - sin ** 2)
        matrix = numpy.array([[cos, -sin], [sin, cos]]) / dmax
        self.data = numpy.array([matrix.dot(i - nose) for i in self.data])

    def _setprofile(self, profile):
        # TODO: control length and depth of array or just get noseindex dynamic//private
        self.data = numpy.array(profile)
        i = 0
        while profile[i+1][0] < profile[i][0] and i < len(profile):
            i += 1
        self.noseindex = i

    def _getprofile(self):
        return self.data

    Profile = property(_getprofile, _setprofile)

_profdata = [[1.00000000e+00,  -1.77114326e-16],
             [5.00000000e-01,   1.73720187e-02],
             [1.33974596e-01,   6.44897990e-02],
             [0.00000000e+00,   0.00000000e+00],
             [1.33974596e-01,  -4.74705844e-02],
             [5.00000000e-01,  -6.58261348e-02],
             [1.00000000e+00,  -2.63677968e-16]]


class Profile2D(BasicProfile2D):
    """Profile2D: 2 Dimensional Standard Profile representative in OpenGlider"""
    #############Initialisation###################
    def __init__(self, profile=_profdata, name="Profile"):
        self.name = name
        if len(profile) > 2:
            # Filter name
            if isinstance(profile[0][0], str):
                self.name = profile[0][0]
                startindex = 1
            else:
                startindex = 0
            self._rootprof = BasicProfile2D(profile[startindex:])
            self._rootprof.normalize()
            self.reset()  # to set the profile

    def __add__(self, other):
        if other.__class__ == self.__class__:
            #use the one with more points
            if self.Numpoints > other.Numpoints:
                first = other.copy()
                second = self
            else:
                first = self.copy()
                second = other

            if not numpy.array_equal(first.XValues, second.XValues):
                first.XValues = second.XValues
            first.Profile = first.Profile + second.Profile * numpy.array([0, 1])
            return first

    def __eq__(self, other):
        return numpy.array_equal(self.Profile, other.Profile)

    def importdat(self, path):
        """Import a *.dat profile"""
        if not os.path.isfile(path):
            raise Exception("Profile not found in"+path+"!")
        tempfile = []
        name = "Profile_Imported"
        pfile = open(path, "r")
        for line in pfile:
            line = line.strip()
            ###tab-seperated values except first line->name
            if "\t" in line:
                line = line.split("\t")
            else:
                line = line.split(" ")
            while "" in line:
                line.remove("")
            if len(line) == 2:
                tempfile.append([float(i) for i in line])
            elif len(line) == 1:
                name = line
        self.__init__(tempfile, name)
        pfile.close()

    def export(self, pfad):
        """Export Profile in .dat Format"""
        out = open(pfad, "w")
        out.write(str(self.name))
        for i in self.Profile:
            out.write("\n" + str(i[0]) + "\t" + str(i[1]))
        return pfad

    def rootpoint(self, xval, h=-1):
        """Get Profile Point for x-value (<0:upper side) optional: height (-1:lower,1:upper);
        use root-profile (highest res)"""
        return self._rootprof.profilepoint(xval, h)

    def reset(self):
        """Reset Profile To Root-Values"""
        self.Profile = self._rootprof.Profile

    def _getxvalues(self):
        """Get XValues of Profile. upper side neg, lower positive"""
        i = self.noseindex
        return numpy.concatenate((self.data[:i, 0]*-1., self.data[i:, 0]))

    def _setxvalues(self, xval):
        """Set X-Values of profile to defined points."""
        ###standard-value: root-prof xvalues
        self.Profile = [self._rootprof(x)[1] for x in xval]
        #self.Profile = self._rootprof.points(xval)[:, 1]

    def _getlen(self):
        return len(self.data)

    def _setlen(self, num):
        """Set Profile to cosinus-Distributed XValues"""
        i = num - num % 2
        xtemp = lambda x: ((x > 0.5)-(x < 0.5))*(1-math.sin(math.pi*x))
        self.XValues = [xtemp(j * 1. / i) for j in range(i + 1)]

    def _getthick(self, *xvals):
        """with no arg the max thick is returned"""
        if not xvals:
            xvals = sorted(set(map(abs, self.XValues)))
        return numpy.array([[i, self.profilepoint(-i)[1][1]-self.profilepoint(i)[1][1]] for i in xvals])

    def _setthick(self, newthick):
        factor = float(newthick/max(self.Thickness[:, 1]))
        new = self.Profile * [1., factor]
        self.__init__(new, self.name + "_" + str(newthick*100) + "%")

    def _getcamber(self, *xvals):
        """return the camber of the profile for certain x-values or if nothing supplied, camber-line"""
        if not xvals:
            xvals = sorted(set(map(abs, self.XValues)))
        return numpy.array([self.profilepoint(i, 0.) for i in xvals])

    def _setcamber(self, newcamber):
        """Set maximal camber to the new value"""
        now = self.Camber
        factor = newcamber/max(now[:,1])-1
        now = dict(now)
        self.__init__([i+[0, now[i[0]]*factor] for i in self.Profile])

    Thickness = property(_getthick, _setthick)
    Numpoints = property(_getlen, _setlen)
    XValues = property(_getxvalues, _setxvalues)
    Camber = property(_getcamber, _setcamber)


# TODO: PYXFOIL INTEGRATION INSTEAD OF THIS
class XFoil(Profile2D):
    """XFoil Calculation Profile based on Profile2D"""

    def __init__(self, profile=""):
        Profile2D.__init__(self, profile)
        self._xvalues = self.XValues
        self._calcvalues = []

    def _change(self):
        """Check if something changed in coordinates"""
        checkval = self._xvalues == self.XValues
        if not isinstance(checkval, bool):
            checkval = checkval.all()
        return checkval

    def _calc(self, angles):

        resfile = "/tmp/result.dat"
        pfile = "/tmp/calc_pfile.dat"
        cfile = Calcfile(angles, resfile)

        self.export(pfile)
        status = os.system("xfoil " + pfile + " <" + cfile + " > /tmp/log.dat")
        if status == 0:
            result = Impresults(resfile)
            for i in result:
                self._calcvalues[i] = result[i]
            os.system("rm " + resfile)
        os.system("rm " + pfile + " " + cfile)

    def _get(self, angle, exact=1):
        if self._change():
            self._calcvalues = {}
            self._xvalues = self.XValues[:]
        print(self._calcvalues)
        calcangles = XValues(angle, self._calcvalues)
        print("ho!" + str(calcangles))
        if len(calcangles) > 0:
            erg = self._calc(calcangles)
            print("soso")
            ##self._calcvalues=[1,2]
        return erg


class Profile3D(Vectorlist):
    def __init__(self, profile=[], name="Profile3d"):
        #Vectorlist.__init__(self, profile, name)
        self._normvectors = self._tangents = False
        self._diff = self._xvekt = self._yvekt = False
        self.data = profile
        self.name = name

    def projection(self):
        if not self._xvekt or not self._yvekt or not self._diff:
            p1 = self.data[0]
            nose = max(self.data, key=lambda x: numpy.linalg.norm(x - p1))
            self.diff = [nose - i for i in self.data]

            xvekt = normalize(self.diff[0])
            yvekt = numpy.array([0, 0, 0])

            for i in self.diff:
                temp = i - xvekt * xvekt.dot(i)
                yvekt = max([yvekt + temp, yvekt - temp], key=lambda x: numpy.linalg.norm(x))

            yvekt = normalize(yvekt)
            self.xvect = xvekt
            self.yvect = yvekt

    def flatten(self):
        """Flatten the Profile and return a 2d-Representative"""
        self.projection()
        return Profile2D([[self.xvekt.dot(i), self.yvekt.dot(i)] for i in self.diff], name=self.Name + "flattened")
        ###find x-y projection-layer first

    def normvectors(self):
        if not self._normvectors:
            self.projection()
            profnorm = numpy.cross(self.xvect, self.yvect)
            func = lambda x: normalize(numpy.cross(x, profnorm))
            vectors = [func(self.data[1]-self.data[0])]
            for i in range(1, len(self.data)-1):
                vectors.append(func(
                    normalize(self.data[i+1]-self.data[i]) +
                    normalize(self.data[i]-self.data[i-1])))
            vectors.append(func(self.data[-1]-self.data[-2]))
            self._normvectors = vectors
        return self._normvectors

    def tangents(self):
        if not self._tangents:
            second = self.data[0]
            third = self.data[1]
            self._tangents = [[normalize(third-second)]]
            for element in self.data[2:-1]:
                first = second
                second = third
                third = element
                self._tangents.append(normalize(normalize(third-second)+normalize(second-first)))
            second = third
            third = self.data[-1]
            self._tangents.append(normalize(third-second))
        return self._tangents



