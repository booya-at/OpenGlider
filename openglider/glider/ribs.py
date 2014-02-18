import math
import numpy
from openglider import Profile2D
from openglider.Profile import Profile3D
from openglider.Utils.cached_property import cached_property
from openglider.glider.ballooning import BallooningBezier
from openglider.Utils.bezier import BezierCurve
from openglider.Vector import rotation_3d

__author__ = 'simon'


class Rib(object):
    """Openglider Rib Class: contains a profile, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition"""
    hashlist = ('_aoa', 'glide', 'arcang', 'zrot', 'chord')  # pos

    def __init__(self, profile=Profile2D(), ballooning=BallooningBezier(), startpoint=numpy.array([0, 0, 0]), size=1.,
                 arcang=0, aoa=0, zrot=0,
                 glide=1, name="unnamed rib", aoaabs=False, startpos=0.):
        # TODO: Startpos > Set Rotation Axis in Percent
        self.name = name
        if isinstance(profile, list):
            self.profile_2d = Profile2D(profile, name=name)
        else:
            self.profile_2d = profile
        self.ballooning = ballooning
        self._aoa = (aoa, aoaabs)
        self.aoa = [0, 0]
        self.glide = glide
        self.arcang = arcang
        self.zrot = zrot
        self.pos = startpoint
        self.chord = size
        #self.profile_3d = None
        #self.rotation_matrix = None
        self._normvectors = None
        #self.profile_3d = Profile3D()
        #self.ReCalc()

    def align(self, point):
        if len(point) == 2:
            return self.align([point[0], point[1], 0])
        elif len(point) == 3:
            return self.pos + self.rotation_matrix.dot(point) * self.chord
        raise ValueError("Can only Align one single 2D or 3D-Point")

    def _setaoa(self, aoa):
        try:
            self._aoa = (aoa[0], bool(aoa[1]))
        except ValueError:
            self._aoa = (float(aoa), False)  # default: relative angle of attack

    def _getaoa(self):
        return dict(zip(["rel", "abs"], self.aoa))  # return in form: ("rel":aoarel,"abs":aoa)

    @property
    def normvectors(self):
        return map(lambda x: self.rotation_matrix.dot([x[0], x[1], 0]), self.profile_2d.normvectors)

    @cached_property('arcang', 'glide', 'zrot', '_aoa')
    def rotation_matrix(self):
        zrot = numpy.arctan(self.arcang) / self.glide * self.zrot
        return rotation_rib(self.aoa[1], self.arcang, zrot)

    @cached_property(*hashlist)
    #@property
    def profile_3d(self):
        if not self.profile_2d.data is None:
            return Profile3D(map(self.align, self.profile_2d.data))
        else:
            return []

    def recalc(self):
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        diff = numpy.arctan(numpy.cos(self.arcang) / self.glide)
        self.aoa[self._aoa[1]] = self._aoa[0]  # self.aoa: (relative, absolute)
        self.aoa[1 - self._aoa[1]] = -diff + self._aoa[0]  # self._aoa: (value, bool: isabsolute)
        # zrot -> ArcTan[Sin[alpha]/gleitzahl]*excel[[i,7]] (relative 1->aligned to airflow)

        self._normvectors = None
        # normvectors 2d->3d->rotated

    def mirror(self):
        self.arcang = -self.arcang
        self.zrot = -self.zrot
        self.pos = numpy.multiply(self.pos, [1, -1., 1])
        #self.ReCalc()

    def copy(self):
        return self.__class__(self.profile_2d.copy(), self.ballooning.copy(), self.pos, self.chord, self.arcang,
                              self._aoa[0], self.zrot,
                              self.glide, self.name + "_copy", self._aoa[1])

    AOA = property(_getaoa, _setaoa)


class MiniRib(Profile3D):
    def __init__(self, yvalue, front_cut, back_cut=1, func=None, name="minirib"):
        #Profile3D.__init__(self, [], name)

        if not func:  # Function is a bezier-function depending on front/back
            if front_cut > 0:
                points = [[front_cut, 1], [front_cut * 2. / 3 + back_cut * 1. / 3]]  #
            else:
                points = [[front_cut, 0]]

            if back_cut < 1:
                points = points + [[front_cut * 1. / 3 + back_cut * 2. / 3, 0], [back_cut, 1]]
            else:
                points = points + [[back_cut, 0]]
            func = BezierCurve(points).interpolation()

        self.__function__ = func

        self.y_value = yvalue
        self.front_cut = front_cut
        self.back_cut = back_cut
        Profile3D.__init__(self, profile=[], name=name)

    def function(self, x):
        if self.front_cut <= abs(x) <= self.back_cut:
            return min(1, max(0, self.__function__(abs(x))))
        else:
            return 1


def rotation_rib(aoa, arc, zrot):
    """Rotation Matrix for Ribs, aoa, arcwide-angle and glidewise angle in radians"""
    # Rotate Arcangle, rotate from lying to standing (x-z)
    rot = rotation_3d(-arc + math.pi / 2, [-1, 0, 0])
    axis = rot.dot([0, 0, 1])
    rot = rotation_3d(aoa, axis).dot(rot)
    axis = rot.dot([0, 1, 0])
    rot = rotation_3d(zrot, axis).dot(rot)
    #rot = rotation_3d(-math.pi/2, [0, 0, 1]).dot(rot)

    return rot