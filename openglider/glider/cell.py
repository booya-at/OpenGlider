
import math
import numpy
from openglider.airfoil import Profile3D
from openglider.glider.ballooning import arsinc
from openglider.vector import norm, normalize, HashedList
from openglider.glider.rib import Rib
from openglider.utils.cached_property import cached_property


class BasicCell(object):
    def __init__(self, prof1=None, prof2=None, ballooning=None, name="unnamed_cell"):
        self.prof1 = prof1 or Profile3D()
        self.prof2 = prof2 or Profile3D()

        if not ballooning is None:
            self.ballooning_phi = ballooning  # ballooning arcs -> property in cell
        self._normvectors = None
        self.name = name

    def point_basic_cell(self, y=0, ik=0):
        ##round ballooning
        return self.midrib_basic_cell(y).point(ik)

    def midrib_basic_cell(self, y, ballooning=True, arc_argument=True):
        if y == 0:              # left side
            return self.prof1
        elif y == 1:            # right side
            return self.prof2
        else:                   # somewhere
            #self._checkxvals()
            midrib = []

            for i in range(len(self.prof1.data)):  # Arc -> phi(bal) -> r  # oder so...
                diff = self.prof1[i] - self.prof2[i]
                if ballooning and self.ballooning_radius[i] > 0.:
                    if arc_argument:
                        d = 0.5 - math.sin(self.ballooning_phi[i] * (0.5 - y)) / math.sin(self.ballooning_phi[i])
                        h = math.cos(self.ballooning_phi[i] * (1 - 2 * y)) - self.ballooning_cos_phi[i]
                        #h = math.sqrt(1 - (norm(diff) * (0.5 - d) / self._radius[i]) ** 2)
                        #h -= self._cosphi[i]  # cosphi2-cosphi
                    else:
                        d = y
                        h = math.sqrt(1 - (norm(diff) * (0.5 - y) / self.ballooning_radius[i]) ** 2)
                        h -= self.ballooning_cos_phi[i]  # cosphi2-cosphi
                else:  # Without ballooning
                    d = y
                    h = 0.
                midrib.append(self.prof1[i] - diff * d + self.normvectors[i] * h * self.ballooning_radius[i])

            return Profile3D(midrib)

    def recalc(self):
        pass
        # Clear everything
        #self._normvectors = None
        #self._calcballooning()

    @cached_property('prof1', 'prof2')  # todo: fix depends (miniribs)
    def normvectors(self, j=None):
        prof1 = self.prof1.data
        prof2 = self.prof2.data
        p1 = self.prof1.tangents
        p2 = self.prof2.tangents
        # cross differenzvektor, tangentialvektor
        return [normalize(numpy.cross(p1[i] + p2[i], prof1[i] - prof2[i])) for i in range(len(prof1))]

    # TODO: raise if len not equal, cache
    @cached_property('ballooning_phi')
    def ballooning_cos_phi(self):
        cos_phi = []
        for phi in self.ballooning_phi:
            if round(phi, 5) > 0:
                cos_phi.append(numpy.cos(phi))
            else:
                cos_phi.append(0)
        return cos_phi

    @cached_property('ballooning_phi', 'prof1', 'prof2')
    def ballooning_radius(self):
        radius = []
        for i, phi in enumerate(self.ballooning_phi):
            if round(phi, 5) > 0:
                radius.append(norm(self.prof1.data[i] - self.prof2.data[i]) / (2*numpy.sin(phi)))
            else:
                radius.append(0)
        return radius

# Ballooning is considered to be arcs, following two simple rules:
# 1: x1 = x*d
# 2: x2 = R*normvekt*(cos(phi2)-cos(phi)
# 3: norm(d)/r*(1-x) = 2*sin(phi(2))


class Cell(BasicCell):
    #TODO: cosmetics
    def __init__(self, rib1=None, rib2=None, miniribs=None):
        self.rib1 = rib1 or Rib()
        self.rib2 = rib2 or Rib()
        self.miniribs = miniribs
        self._yvalues = []
        self._cells = []
        BasicCell.__init__(self, self.rib1.profile_3d, self.rib2.profile_3d)

    def recalc(self):
        if not self.rib2.profile_2d.numpoints == self.rib1.profile_2d.numpoints:
            raise ValueError("Unequal length of Cell-Profiles")
        xvalues = self.rib1.profile_2d.x_values
        BasicCell.recalc(self)
        self.prof1 = self.rib1.profile_3d
        self.prof2 = self.rib2.profile_3d
        #Map Ballooning

        if not self.miniribs:  # In case there is no midrib, The Cell represents itself!
            self._cells = [self]  # The cell itself is its cell, clear?
            self._yvalues = [0, 1]
        else:
            self._cells = []
            self._yvalues = [0] + [rib.y_value for rib in self.miniribs] + [1]
            ballooning = [self.rib1.ballooning[x] + self.rib2.ballooning[x] for x in xvalues]
            miniribs = sorted(self.miniribs, key=lambda rib: rib.y_value)  # sort for cell-wide (y) argument.

            first = self.rib1.profile_3d
            for minirib in miniribs:
                big = self.midrib_basic_cell(minirib.y_value, True).data
                small = self.midrib_basic_cell(minirib.y_value, False).data
                points = []

                for i in range(len(big)):  # Calculate Rib
                    fakt = minirib.function(xvalues[i])  # factor ballooned/unb. (0-1)
                    point = small[i] + fakt * (big[i] - small[i])
                    points.append(point)

                minirib.data = points
                second = minirib
                self._cells.append(BasicCell(first, second, []))  # leave ballooning empty
                first = second
            #Last Sub-Cell
            self._cells.append(BasicCell(first, self.rib2.profile_3d, []))

            # Calculate ballooning for each x-value
            # Hamilton Principle:
            #       http://en.wikipedia.org/wiki/Hamilton%27s_principle
            #       http://en.wikipedia.org/wiki/Hamilton%E2%80%93Jacobi_equation
            # b' = b
            # f' = f*(l/l') [f=b/l]
            for i in range(len(first.data)):
                bl = ballooning[i] + 1  # b/l -> *l/lnew
                l = norm(self.rib2.profile_3d.data[i] - self.rib1.profile_3d.data[i])  # L
                lnew = sum([norm(c.prof1.data[i] - c.prof2.data[i]) for c in self._cells])  # L-NEW
                for c in self._cells:
                    newval = lnew / l / bl
                    if newval < 1.:
                        c.ballooning_phi.append(arsinc(newval))  # B/L NEW 1 / (bl * l / lnew)
                    else:
                        c.ballooning_phi.append(arsinc(1.))
                        #raise ValueError("mull")
            for cell in self._cells:
                cell.recalc()

    def point(self, y=0, i=0, k=0):
        return self.midrib(y).point(i, k)

    def midrib(self, y, ballooning=True, arc_argument=False):
        if len(self._cells) == 1:
            return self.midrib_basic_cell(y, ballooning=ballooning)
        if ballooning:
            i = 0
            while self._yvalues[i + 1] < y:
                i += 1
            cell = self._cells[i]
            y_new = (y - self._yvalues[i]) / (self._yvalues[i + 1] - self._yvalues[i])
            return cell.midrib_basic_cell(y_new, arc_argument=arc_argument)
        else:
            return self.midrib_basic_cell(y, ballooning=False)

    @cached_property('rib1.ballooning', 'rib2.ballooning')
    def ballooning_phi(self):
        x_values = self.rib1.profile_2d.x_values
        balloon = [self.rib1.ballooning[i] + self.rib2.ballooning[i] for i in x_values]
        return HashedList([arsinc(1. / (1+bal)) for bal in balloon])

    @property
    def ribs(self):
        return [self.rib1, self.rib2]

    @property
    def span(self):  # TODO: Maybe use mean length from (1,0), (0,0)
        return norm((self.rib1.pos - self.rib2.pos) * [0, 1, 1])

    @property
    def area(self):
        p1_1 = self.rib1.align([0, 0, 0])
        p1_2 = self.rib1.align([1, 0, 0])
        p2_1 = self.rib2.align([0, 0, 0])
        p2_2 = self.rib2.align([1, 0, 0])
        return 0.5 * (norm(numpy.cross(p1_2 - p1_1, p2_1 - p1_1)) + norm(numpy.cross(p2_2 - p2_1, p2_2 - p1_2)))

    @property
    def aspect_ratio(self):
        return self.span ** 2 / self.area
