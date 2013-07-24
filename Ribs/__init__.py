from .move import rotation#, alignment
from Profile import Profile2D, XFoil
import numpy


class rib(object):
    """docstring for rib"""

    def __init__(self, profile="", startpoint=numpy.array([0, 0, 0]), alpha="", aoa="", gamma="", glide="", name="unnamed rib",
                 startpos=0.):
        self.name = name
        if isinstance(profile, list):
            self.profile2D = Profile2D(profile, name=name)

        self._change = False
        self._glide=glide


    def Get3D(self):
        if self._change:
            self.Profile3D = ""#Profile.Profile3D(self.profile, )


    def Align(self, points):
        if self._change:
            self._rot = rotation(self.alpha, self.aoa_abs, self.gamma)
            offset = numpy.array([-self.startpos * self.chord, 0, 0])
            #self._pos = alignment(self.startpoint + offset)
        return self._pos(self._rot(points))

    def _SetVal(self, which, value):
        if which in self.__dict__:
            self.__dict__[which] = value
            self._change = True

    def _GetVal(self, which):
        if which in self.__dict__:
            return self.__dict__[which]
        else:
            raise "schas"
