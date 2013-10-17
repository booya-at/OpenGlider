__author__ = 'simon'
import Ribs
import numpy


class basiccell(object):
    def __init__(self, rib1=Ribs.Rib(), rib2=Ribs.Rib()):
        self.rib1=rib1
        self.rib2=rib2

    def point(self, x=0, y=0):
        if not

        ##round ballooning
        if x==0:
            return self.rib1.profile_3d.point(self.rib1.profile_2d.profilepoint(y)[1:])
        elif x==1:
            return self.rib2.profile_3d.point(self.rib2.profile_2d.profilepoint(y)[1:])
        else:
            midrib=self.midrib(x)
            return midrib

    def midrib(self,y):
        self._checkxvals()


    def _checkxvals(self):
        if not numpy.allclose(self.rib1.profile_2d.XValues,self.rib2.profile_2d.XValues):
            self.rib1.profile_2d.XValues=self.rib2.profile_2d.XValues
            self.rib1.ReCalc()