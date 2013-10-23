__author__ = 'simon'
import openglider.Ribs as Ribs
import numpy
from ..Vector import normalize
from ..Profile import Profile3D

class BasicCell(object):
    def __init__(self, rib1=Profile3D(), rib2=Profile3D(), ballooning=[]):
        self.prof1 = rib1
        self.prof2 = rib2
        self.ballooning_mapped = ballooning

    def point(self, x=0, i=0, k=0):
        ##round ballooning
        return self.midrib(x).point((i, k))

    def midrib(self, x, ballooning=True):
        if x == 0:
            return self.prof1
        elif x == 1:
            return self.prof2
        else:
            #self._checkxvals()

            midrib = []
            prof1 = self.prof1.data
            prof2 = self.prof2.data

            if ballooning:
                normvectors = self.normvectors()
                func = lambda i: prof1[i]+x*(prof2[i]-prof1[i])
            else:
                func = lambda i: prof1[i]+x*(prof2[i]-prof1[i])

            for i in range(len(self.prof1)):  # Arc -> phi(bal) -> r  # oder so...
                midrib.append(func(i))
            return Profile3D(midrib)

    def normvectors(self):
        try:
            return self._normvectors
        except ValueError:
            p1 = self.prof1.normvectors()
            p2 = self.prof2.normvectors()
            self._normvectors = [normalize(p1[i]+p2[i]) for i in range(len(p1))]
            return self._normvectors


class Cell(BasicCell):
    def __init__(self, rib1=Ribs.Rib(), rib2=Ribs.Rib(),miniribs=[]):
        self.rib1 = rib1
        self.rib2 = rib2
        self.prof1 = self.rib1.profile_3d
        self.prof2 = self.rib2.profile_3d
        self.prof1._normvectors = self.rib1.normvectors()
        self.prof2._normvectors = self.rib2.normvectors()
        self.miniribs=miniribs

    def recalc(self):
        if len(self.miniribs) == 0:
            self._cells = [self]
        else:
            self.miniribs.sort(key=lambda x: (x[2]-0.5)**2)  # from the middle towards the outside









"""
    def _checkxvals(self):
        #####TODO: push to normal cell.
        if not numpy.allclose(self.rib1.profile_2d.XValues, self.rib2.profile_2d.XValues):
            self.rib2.profile_2d.XValues = self.rib1.profile_2d.XValues
            self.rib2.ReCalc()
            redo = True
        else:
            redo = False
        if redo or not self.normvectors:
            self.normvectors = [normalize(self.rib1.normvectors[i]+self.rib2.normvectors[i])
                                for i in range(self.rib1.profile_2d.Numpoints)]
            #TODO: map balooning
            """