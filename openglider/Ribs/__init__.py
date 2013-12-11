from openglider.Ribs.move import rotation#, alignment
from openglider.Profile import Profile2D, Profile3D
from openglider.Utils.Ballooning import BallooningBezier
import numpy
from ..Vector import arrtype
from openglider.Utils.Bezier import BezierCurve


class Rib(object):
    """Openglider Rib Class: contains a profile, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition"""
    def __init__(self, profile=Profile2D(), ballooning=BallooningBezier(), startpoint=numpy.array([0, 0, 0]), size=1., arcang=0, aoa=0, zrot=0,
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
        self.size = size
        
        #self.ReCalc()

    def align(self, points):
        ptype = arrtype(points)
        if ptype == 1:
            return self.pos+self._rot.dot([points[0]*self.size, points[1]*self.size, 0])
        if ptype == 2 or ptype == 4:
            return [self.align(i) for i in points]
        if ptype == 3:
            return self._rot.dot(numpy.array([self.size, self.size, 0])*points)
    
    def _setaoa(self, aoa):
        try:
            self._aoa = (aoa[0], bool(aoa[1]))
        except ValueError:
            self._aoa = (float(aoa), False)  # default: relative angle of attack

    def _getaoa(self):
        return dict(zip(["rel", "abs"], self.aoa))  # return in form: ("rel":aoarel,"abs":aoa)

    def recalc(self):
        ##recalc aoa_abs/rel
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        diff = numpy.arctan(numpy.cos(self.arcang)/self.glide)
        ##aoa->(rel,abs)
        #########checkdas!!!!!
        self.aoa[self._aoa[1]] = self._aoa[0]  # first one is relative
        self.aoa[1-self._aoa[1]] = diff+self._aoa[0]  # second one absolute

        self._rot = rotation(self.aoa[1], self.arcang, self.zrot)
        self.profile_3d = Profile3D(self.align(self.profile_2d.Profile))
        self.normvectors = map(lambda x: self._rot.dot([x[0], x[1], 0]), self.profile_2d.normvectors())  # normvectors 2d->3d->rotated

    def mirror(self):
        self.arcang = -self.arcang
        self.zrot = -self.zrot
        self.pos = numpy.multiply(self.pos,[-1.,1,1])
        #self.ReCalc()

    def copy(self):
        return self.__class__(self.profile_2d.copy(), self.ballooning.copy(), self.pos, self.size, self.arcang, self._aoa[0], self.zrot,
                              self.glide, self.name + "_copy", self._aoa[1])

    AOA = property(_getaoa, _setaoa)


class MiniRib(Profile3D):
    def __init__(self, xvalue, front_cut, back_cut, func=None, name="minirib"):
        #Profile3D.__init__(self, [], name)

        if not func:  # Function is a bezier-function depending on front/back
            if front_cut > 0:
                points = [[front_cut, 1], [front_cut*2./3+back_cut*1./3]]  #
            else:
                points = [[front_cut, 0]]

            if back_cut < 1:
                points = points + [[front_cut*1./3+back_cut*2./3, 0], [back_cut, 1]]
            else:
                points = points + [[back_cut, 0]]
            func = BezierCurve(points).interpolation()

        self.__function__ = func

        self.xvalue = xvalue
        self.front_cut = front_cut
        self.back_cut = back_cut
        Profile3D.__init__(self, profile=[], name=name)

    def function(self, x):
        if self.front_cut <= abs(x) <= self.back_cut:
            return min(1, max(0, self.__function__(abs(x))))
        else:
            return 1