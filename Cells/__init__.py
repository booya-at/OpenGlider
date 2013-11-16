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

        self._phi = ballooning  # ballooning arcs
        self._cosphi = self._radius = None

        prof1 = prof1.data
        prof2 = prof2.data
        p1 = self.prof1.tangents()
        p2 = self.prof2.tangents()
        # cross differenzvektor, tangentialvektor
        self._normvectors = [-normalize(numpy.cross(p1[i]+p2[i], prof1[i]-prof2[i])) for i in range(len(p1))]

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

            _horizontal = lambda xx, j: prof1[j]+xx*(prof2[j]-prof1[j])

            if ballooning:
                self._calcballooning()

                def func(xx, j):
                    r = self._radius[j]
                    if r > 0:
                        cosphi = self._cosphi[j][0]
                        d = prof2[j]-prof1[j]
                        #phi=math.asin(norm(d)/(2*r)*(x-1/2)) -> cosphi=sqrt(1-(norm(d)/r*(x+1/2))^2
                        cosphi2 = math.sqrt(1-(norm(d)*(0.5-xx)/r)**2)
                        return prof1[j]+xx*d + self._normvectors[j]*(cosphi2-cosphi)*r
                    else:
                        return _horizontal(xx, j)
            else:
                func = _horizontal

            for i in range(len(self.prof1.data)):  # Arc -> phi(bal) -> r  # oder so...
                midrib.append(func(x, i))
            return Profile3D(midrib)

    def _calcballooning(self):
        if not self._cosphi and not self._radius:
            self._cosphi = []
            self._radius = []
            if len(self._phi) == len(self.prof1.data) == len(self.prof2.data):
                for i in range(len(self._phi)):
                    if round(self._phi[i], 5) > 0:
                        self._cosphi.append(numpy.cos(self._phi[i]))
                        self._radius.append(norm(self.prof1.data[i]-self.prof2.data[i])/(2*numpy.sin(self._phi[i])))
                    else:
                        self._cosphi.append(0)
                        self._radius.append(0)
            else:
                raise "length of ballooning/profile data unequal"


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
        
        self.prof1 = self.rib1.profile_3d
        self.prof2 = self.rib2.profile_3d
        self.miniribs = miniribs

        # inheritance backup
        super.__init__(self.rib1.profile_3d, self.rib2.profile_3d, [])
        self._midrib = self.midrib
        self._point = self.point

    def recalc(self):
        xvalues = self.rib1.profile_2d.XValues
        if len(self.miniribs) == 0:  # In case there is no midrib, The Cell represents itself!
            self._cells = [BasicCell(self.prof1, self.prof2,)]
            self._yvalues = [0, 1]
        else:
            self._cells = []
            miniribs = sorted(self.miniribs, key=lambda x: x.xvalue)    # sort for cell-wide (x) argument.
            self._yvalues = [i.xvalue for i in miniribs]

            prof1 = self.rib1.profile_3d
            for minirib in miniribs:

                big = self.midrib(minirib.xvalue, True).data  # SUPER!!!?
                small = self.midrib(minirib.xvalue, False).data
                #phi1 = []

                for i in range(len(big.data)):  # Calculate Rib
                    fakt = minirib.function(xvalues[i])  # factor ballooned/unb. (0-1)
                    point = small[i]+fakt*(big[i]-small[i])
                    minirib.data.append(point)

                prof2 = minirib
                self._cells.append(BasicCell(prof1, prof2, []))  # leace ballooning empty
                prof1 = prof2

            self._cells.append(BasicCell(prof1, self.rib2.profile_3d))

            for i in range(len(prof1.data)):    # Calculate ballooning for each x-value
                bl = self._ballooning[i]
                l = norm(self.prof2.data[i]-self.prof1.data[i])
                lnew = sum([norm(c.prof1.data[i]-c.prof2.data[i]) for c in self._cells])
                for c in self._cells:
                    c._ballooning.append(bl*l/lnew)


#            for i in range(len(big.data)):  # Calculate Ballooning for each subcell

#                yvalue = minirib.xvalue




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