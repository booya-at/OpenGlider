__author__ = 'simon'
import openglider.Ribs as Ribs
import numpy
from ..Vector import normalize
from ..Profile import Profile3D

class BasicCell(object):
    def __init__(self, rib1=Ribs.Rib(), rib2=Ribs.Rib()):
        self.rib1 = rib1
        self.rib2 = rib2
        self.rib1.ReCalc()
        self._checkxvals()

    def point(self, x=0, y=0):
        ##round ballooning
            return midrib(x).point(y)

    def midrib(self, y):
        self._checkxvals()

    def _checkxvals(self):
        if not numpy.allclose(self.rib1.profile_2d.XValues, self.rib2.profile_2d.XValues):
            self.rib2.profile_2d.XValues = self.rib1.profile_2d.XValues
            self.rib2.ReCalc()
            redo = True
        else:
            redo = False
        if redo or not self.normvectors:
            self.normvectors = [normalize(normalize(self.rib1.normvectors()[i]) +
                                          normalize(self.rib2.normvectors()[i]))
                                for i in range(self.rib1.profile_2d.Numpoints)]

    def midrib(self, x):
        if x == 0:
            return self.rib1.profile_3d
        elif x == 1:
            return self.rib2.profile_3d
        else:
            self._checkxvals()

            midrib = []
            prof1 = self.rib1.profile_3d.data
            prof2 = self.rib2.profile_3d.data
            bal=[1,2,3]
            for i in range(self.rib1.profile_2d.Numpoints):  # Arc -> phi(bal) -> r
                point = prof1[i]+x*(prof2[i]-prof1[i])+self.normvectors[i]*(numpy.cos(x-0.5))  # oder so...
                midrib.append(point)
            return Profile3D(midrib)