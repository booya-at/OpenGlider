from openglider.Ribs.move import rotation#, alignment
from openglider.Profile import Profile2D, Profile3D
import numpy
from ..Vector import arrtype


class Rib(object):
    """Openglider Rib Class: contains a profile, needs a startpoint, angle (arcwide), angle of attack,
        glide-wide rotation and glider ratio.
        optional: name, absolute aoa (bool), startposition"""
    def __init__(self, profile=Profile2D(), startpoint=numpy.array([0, 0, 0]), length=1.,arcang=0, aoa=0, zrot=0, glide=1,
                 name="unnamed rib", aoaabs=False, startpos=0.):
        self.name = name
        if isinstance(profile, list):
            self.profile_2d = Profile2D(profile, name=name)
        else:
            self.profile_2d = profile
        self._aoa = (aoa, aoaabs)
        self.aoa = [0, 0]
        self.glide = glide
        self.arcang = arcang
        self.zrot = zrot
        self.pos = startpoint
        self.length = length
        
        #self.ReCalc()


    def Align(self, points):
        ptype=arrtype(points)
        if ptype == 1:
            return self.pos+self._rot.dot([points[0]*self.length,points[1]*self.length,0])
        if ptype == 2 or ptype == 4:
            return [self.Align(i) for i in points]
        if ptype == 3:
            return self._rot.dot(numpy.array([self.length,self.length,0])*points)
    
    def _SetAOA(self, aoa):
        try:
            self._aoa = (aoa[0], bool(aoa[1]))
        except ValueError:
            self._aoa = (float(aoa), False)  # default: relative angle of attack

    def _GetAOA(self):
        return dict(zip(["rel", "abs"], self.aoa))  # return in form: ("rel":aoarel,"abs":aoa)

    def ReCalc(self):
        ##recalc aoa_abs/rel
        ##Formula for aoa rel/abs: ArcTan[Cos[alpha]/gleitzahl]-aoa[rad];
        diff = numpy.arctan(numpy.cos(self.arcang)/self.glide)
        ##aoa->(rel,abs)
        #########checkdas!!!!!
        self.aoa[self._aoa[1]] = self._aoa[0]  # first one is relative
        self.aoa[1-self._aoa[1]] = diff+self._aoa[0]  # second one absolute

        self._rot = rotation(self.aoa[1], self.arcang, self.zrot)
        self.profile_3d = Profile3D(self.Align(self.profile_2d.Profile))
        self.normvectors = map(lambda x: self._rot.dot([x[0], x[1], 0]), self.profile_2d.normvectors())  # normvectors 2d->3d->rotated

    def mirror(self):
        self.arcang = -self.arcang
        self.zrot = -self.zrot
        self.pos = numpy.multiply(self.pos,[-1.,1,1])
        #self.ReCalc()

    def copy(self):
        return self.__class__(self.profile_2d.copy(), self.pos, self.length, self.arcang, self._aoa[0], self.zrot, self.glide,
                              self.name + "_copy", self._aoa[1])

    AOA = property(_GetAOA, _SetAOA)
        
