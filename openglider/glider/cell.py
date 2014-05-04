import copy
import math
import numpy
import itertools
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

    def copy(self):
        return copy.deepcopy(self)

    midrib = midrib_basic_cell

# Ballooning is considered to be arcs, following two simple rules:
# 1: x1 = x*d
# 2: x2 = R*normvekt*(cos(phi2)-cos(phi)
# 3: norm(d)/r*(1-x) = 2*sin(phi(2))


class Cell():
    def __init__(self, rib1, rib2, miniribs=None):
        #self.miniribs = miniribs and miniribs or []
        self._ribs = [rib1, rib2]
        self._miniribs = []
        self.x_values = rib1.profile_2d.x_values
        self._basic_cell = BasicCell(rib1.profile_3d, rib2.profile_3d, ballooning=self.ballooning_phi)

    def add_minirib(self, minirib):
        """add a minirib to the cell.
         Minirib should be within borders, otherwise a ValueError will be thrown
         profile:
        """
        self._miniribs.append(minirib)

    @cached_property('rib1', 'rib2')
    def basic_cell(self):
        return BasicCell(self.rib1.profile_3d, self.rib2.profile_3d, self.ballooning_phi)

    @cached_property('_miniribs', '_ribs')
    def rib_profiles_3d(self):
        midrib_profiles = [self._make_profile3d_from_minirib(mrib)
                           for mrib in self._miniribs]
        rib_profiles = [rib.profile_3d for rib in self._ribs]
        return [rib_profiles[0]] + midrib_profiles + [rib_profiles[1]]

    def _make_profile3d_from_minirib(self, minirib):
        self.basic_cell.prof1 = self.prof1
        self.basic_cell.prof2 = self.prof2
        shape_with_ballooning = self.basic_cell.midrib_basic_cell(self, minirib.y_value,
                                                                   True).data
        shape_without_ballooning = self.basic_cell.midrib_basic_cell(minirib.y_value,
                                                                      True).data
        points = []
        for xval, with_bal, without_bal in itertools.izip(
                self.x_values, shape_with_ballooning, shape_without_ballooning
        ):
                fakt = minirib.function(xval)  # factor ballooned/unb. (0-1)
                point = without_bal + fakt * (with_bal - without_bal)
                points.append(point)
        return Profile3D(points)

    @cached_property('rib_profiles_3d')
    def _child_cells(self):
        """get all the child cells within the current cell,
         defined by the miniribs
        """
        cells = []
        for leftrib, rightrib in\
                itertools.izip(self.rib_profiles_3d[:-1], self.rib_profiles_3d[1:]):
            cells.append(BasicCell(leftrib, rightrib))
        if not self._miniribs:
            return cells
        ballooning = [self.rib1.ballooning[x] + self.rib2.ballooning[x] for x in self.x_values]
        #for i in range(len(first.data)):
        for index, (bl, left_point, right_point) in enumerate(itertools.izip(
            ballooning, self._ribs[0].profile_3d.data, self._ribs[1].profile_3d.data
        )):
            l = norm(right_point - left_point)  # L
            lnew = sum([norm(c.prof1.data[index] - c.prof2.data[index]) for c in cells])  # L-NEW
            for c in self._child_cells:
                newval = lnew / l / bl
                if newval < 1.:
                    c.ballooning_phi.append(arsinc(newval))  # B/L NEW 1 / (bl * l / lnew)
                else:
                    c.ballooning_phi.append(arsinc(1.))
                    #raise ValueError("mull")
        return cells

    @property
    def rib1(self):
        return self._ribs[0]

    @rib1.setter
    def rib1(self, rib):
        self._ribs[0] = rib

    @property
    def rib2(self):
        return self._ribs[1]

    @rib2.setter
    def rib2(self, rib):
        self._ribs[1] = rib

    @property
    def _yvalues(self):
        return [0] + [mrib.y_value for mrib in self._miniribs] + [1]

    @property
    def prof1(self):
        return self.rib1.profile_3d

    @property
    def prof2(self):
        return self.rib2.profile_3d

    def point(self, y=0, i=0, k=0):
        return self.midrib(y).point(i, k)

    def midrib(self, y, ballooning=True, arc_argument=False):
        if len(self._child_cells) == 1:
            return self.basic_cell.midrib_basic_cell(y, ballooning=ballooning)
        if ballooning:
            i = 0
            while self._yvalues[i + 1] < y:
                i += 1
            cell = self._child_cells[i]
            y_new = (y - self._yvalues[i]) / (self._yvalues[i + 1] - self._yvalues[i])
            return cell.midrib_basic_cell(y_new, arc_argument=arc_argument)
        else:
            return self.basic_cell.midrib_basic_cell(y, ballooning=False)

    @cached_property('rib1.ballooning', 'rib2.ballooning')
    def ballooning_phi(self):
        x_values = self.rib1.profile_2d.x_values
        balloon = [self.rib1.ballooning[i] + self.rib2.ballooning[i] for i in x_values]
        return HashedList([arsinc(1. / (1+bal)) for bal in balloon])

    #TODO: check for usages
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

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self):
        self.rib2, self.rib1 = self.rib1, self.rib2
        for rib in self.ribs:
            rib.mirror()