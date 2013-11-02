__author__ = 'simon'
import openglider.Ribs as Ribs
import numpy
from ..Vector import normalize, norm
from ..Profile import Profile3D
from ..Utils import Ballooning
import math


class BasicCell(object):
    def __init__(self, prof1=Profile3D(), prof2=Profile3D(), ballooning=[]):
        self.prof1 = prof1
        self.prof2 = prof2
        self._ballooning = []
        for i in range(len(ballooning)):
            if round(ballooning[i], 5) > 0:
                self._ballooning.append([numpy.cos(ballooning[i]),
                                         norm(prof1.data[i]-prof2.data[i])/(2*numpy.sin(ballooning[i]))])
            else:
                self._ballooning.append([0, 0])

        prof1=prof1.data
        prof2=prof2.data
        p1 = self.prof1.tangents()
        p2 = self.prof2.tangents()
        # cross differenzvektor, tangentialvektor
        self._normvectors = [-numpy.cross(p1[i]+p2[i], prof1[i]-prof2[i]) for i in range(len(p1))]
        #print(map(norm, self._normvectors))
        #print("hoho",self._normvectors)
        #print(self._normvectors)

    def point(self, x=0, i=0, k=0):
        ##round ballooning
        return self.midrib(x).point((i, k))

    def midrib(self, x, ballooning=True):
        if x == 0:              # left side
            return self.prof1
        elif x == 1:            # right side
            return self.prof2
        else:                   # somewhere
            #self._checkxvals()
            midrib = []
            prof1 = self.prof1.data
            prof2 = self.prof2.data

            _horizontal = lambda j: prof1[j]+x*(prof2[j]-prof1[j])

            if ballooning:
                def func(j):
                    r = self._ballooning[j][1]
                    if r > 0:
                        cosphi = self._ballooning[j][0]
                        d = prof2[j]-prof1[j]
                        #phi=math.asin(norm(d)/(2*r)*(x-1/2)) -> cosphi=sqrt(1-(norm(d)/r*(x+1/2))^2
                        cosphi2 = math.sqrt(1-(norm(d)*(0.5-x)/r)**2)
                        #print((cosphi2,cosphi,x+1/2))
                        return prof1[j]+x*d + self._normvectors[j]*(cosphi2-cosphi)*r
                    else:
                        return _horizontal(j)
            else:
                func = _horizontal

            for i in range(len(self.prof1.data)):  # Arc -> phi(bal) -> r  # oder so...
                midrib.append(func(i))
            return Profile3D(midrib)

"""
Ballooning is considered to be arcs, following two simple rules:
1: x1 = x*d
2: x2 = R*normvekt*(cos(phi2)-cos(phi)
3: norm(d)/r*(1-x) = 2*sin(phi(2))
"""

class Cell(BasicCell):
    def __init__(self, rib1=Ribs.Rib(), rib2=Ribs.Rib(), miniribs=[]):
        self.rib1 = rib1
        self.rib2 = rib2
        #if not self.rib1.profile_2d.Numpoints == self.rib2.profile_2d.Numpoints:

        #ballooning=rib1.ballooning
        super.__init__(self.rib1.profile_3d, self.rib2.profile_3d, [])
        self.prof1 = self.rib1.profile_3d
        self.prof2 = self.rib2.profile_3d
        self.prof1._normvectors = self.rib1.normvectors()
        self.prof2._normvectors = self.rib2.normvectors()
        self.miniribs = miniribs


    def recalc(self):
        self.xvalues=self.rib1.profile_2d.XValues
        if len(self.miniribs) == 0:
            self._cells = [BasicCell(self.prof1, self.prof2,)]
        else:
            self._cells = []
            miniribs=sorted(self.miniribs,key=lambda x: x[0])  # sort for cell-wide (x) argument. second value is function
            # MINIRIB CONVENTION: X-value(cell-wide), Front
            miniribs.append([1., lambda: 0])
            for rib in miniribs:
                big=self.midrib(rib[0],True).data  # SUPER!!!?
                small=self.midrib(rib[0],False).data
                #midrib=[rib[1](self.xvalues[i])*(big[i]-small[i])+small[i]+for i in range(len(big.data))]
                self._cells.append(BasicCell())

            # super??


    # def minirib(self, x, front = 0, back = 1, lenfront = 0, lenback = 0):










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