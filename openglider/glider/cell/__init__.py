import copy
import math
import itertools

import numpy

from openglider.airfoil import Profile3D, Profile2D
from openglider.glider.ballooning import Ballooning
from openglider.utils import consistent_value
from openglider.utils.cache import cached_property, CachedObject, HashedList
from openglider.vector.functions import normalize

from .elements import *


class BasicCell(CachedObject):
    """
    A very simple cell without any extras like midribs, diagonals,..
    """
    def __init__(self, prof1=None, prof2=None, ballooning=None, name="unnamed_cell"):
        self.prof1 = prof1 or Profile3D([])
        self.prof2 = prof2 or Profile3D([])

        if ballooning is not None:
            self.ballooning_phi = ballooning  # ballooning arcs -> property in cell
        self.name = name

    def point_basic_cell(self, y=0, ik=0):
        ##round ballooning
        return self.midrib(y).point(ik)

    def midrib(self, y_value, ballooning=True, arc_argument=True):
        if y_value == 0:              # left side
            return self.prof1
        elif y_value == 1:            # right side
            return self.prof2
        else:                   # somewhere else
            #self._checkxvals()
            midrib = []

            for i in range(len(self.prof1.data)):  # Arc -> phi(bal) -> r  # oder so...
                diff = self.prof1[i] - self.prof2[i]
                if ballooning and self.ballooning_radius[i] > 0.:
                    if arc_argument:
                        # d = 0.5 - math.sin(self.ballooning_phi[i] * (y_value- 0.5)) / math.sin(self.ballooning_phi[i])
                        d = 0.5 - math.sin(self.ballooning_phi[i] * (1 - 2 *  y_value)) / math.sin(self.ballooning_phi[i]) / 2
                        h = math.cos(self.ballooning_phi[i] * (1 - 2 * y_value)) - self.ballooning_cos_phi[i]
                        #h = math.sqrt(1 - (norm(diff) * (0.5 - d) / self._radius[i]) ** 2)
                        #h -= self._cosphi[i]  # cosphi2-cosphi
                    else:
                        d = y_value
                        # h = math.sqrt(1 - (norm(diff) * (0.5 - y_value) ** 2 / self.ballooning_radius[i]) ** 2)
                        # h -= self.ballooning_cos_phi[i]  # cosphi2-cosphi
                        h = math.cos(math.asin((2 * d - 1)*math.sin(self.ballooning_phi[i]))) -  math.cos(self.ballooning_phi[i])
                else:  # Without ballooning
                    d = y_value
                    h = 0.
                midrib.append(self.prof1[i] - diff * d +
                              self.normvectors[i] * h * self.ballooning_radius[i])

            return Profile3D(midrib)

    @cached_property('prof1', 'prof2')
    def normvectors(self, j=None):
        prof1 = self.prof1.data
        prof2 = self.prof2.data
        p1 = self.prof1.tangents
        p2 = self.prof2.tangents
        # cross differenzvektor, tangentialvektor
        return [normalize(numpy.cross(p1[i] + p2[i], prof1[i] - prof2[i])) for i in range(len(prof1))]

    @cached_property('ballooning_phi')
    def ballooning_cos_phi(self):
        tolerance = 0.00001
        return [numpy.cos(phi) if phi > tolerance else 0 for phi in self.ballooning_phi]

    @cached_property('ballooning_phi', 'prof1', 'prof2')
    def ballooning_radius(self):
        tolerance = 0.00001
        return [norm(p1-p2)/(2*numpy.sin(phi)) if phi>tolerance else 0
                for p1, p2, phi in zip(self.prof1, self.prof2, self.ballooning_phi)]
        # radius = []
        # for i, phi in enumerate(self.ballooning_phi):
        #     if round(phi, 5) > 0:
        #         radius.append(norm(self.prof1.data[i] - self.prof2.data[i]) / (2*numpy.sin(phi)))
        #     else:
        #         radius.append(0)
        # return radius

    def copy(self):
        return copy.deepcopy(self)


# Ballooning is considered to be arcs, following 2 (two!) simple rules:
# 1: x1 = x*d
# 2: x2 = R*normvekt*(cos(phi2)-cos(phi)
# 3: norm(d)/r*(1-x) = 2*sin(phi(2))


class Cell(CachedObject):
    def __init__(self, rib1, rib2, ballooning, miniribs=None, panels=None, diagonals=None):
        self.rib1 = rib1
        self.rib2 = rib2
        self._miniribs = miniribs or []
        self.diagonals = diagonals or []
        self.ballooning = ballooning
        self.panels = panels or []

    def __json__(self):
        return {"rib1": self.rib1,
                "rib2": self.rib2,
                "ballooning": self.ballooning,
                "miniribs": self._miniribs,
                "diagonals": self.diagonals,
                "panels": self.panels}

    def add_minirib(self, minirib):
        """add a minirib to the cell.
         Minirib should be within borders, otherwise a ValueError will be thrown
         profile:
        """
        self._miniribs.append(minirib)

    @cached_property('rib1.profile_3d', 'rib2.profile_3d', 'ballooning_phi')
    def basic_cell(self):
        return BasicCell(self.rib1.profile_3d, self.rib2.profile_3d, self.ballooning_phi)

    @cached_property('_miniribs', 'rib1', 'rib2')
    def rib_profiles_3d(self):
        """
        Get all the ribs 3d-profiles, including miniribs
        """
        profiles = [self.rib1.profile_3d]
        profiles += [self._make_profile3d_from_minirib(mrib) for mrib in self._miniribs]
        profiles += [self.rib2.profile_3d]

        return profiles

    def _make_profile3d_from_minirib(self, minirib):
        # self.basic_cell.prof1 = self.prof1
        # self.basic_cell.prof2 = self.prof2
        shape_with_ballooning = self.basic_cell.midrib(minirib.y_value,
                                                       True).data
        shape_without_ballooning = self.basic_cell.midrib(minirib.y_value,
                                                          True).data
        points = []
        for xval, with_bal, without_bal in zip(
                self.x_values, shape_with_ballooning, shape_without_ballooning):
            fakt = minirib.function(xval)  # factor ballooned/unb. (0-1)
            point = without_bal + fakt * (with_bal - without_bal)
            points.append(point)
        return Profile3D(points)

    @cached_property('rib_profiles_3d')
    def _child_cells(self):
        """
        get all the sub-cells within the current cell,
        (separated by miniribs)
        """
        cells = []
        for leftrib, rightrib in zip(self.rib_profiles_3d[:-1], self.rib_profiles_3d[1:]):
            cells.append(BasicCell(leftrib, rightrib, ballooning=[]))
        if not self._miniribs:
            return cells
        ballooning = [self.rib1.ballooning[x] + self.rib2.ballooning[x] for x in self.x_values]
        #for i in range(len(first.data)):
        for index, (bl, left_point, right_point) in enumerate(itertools.izip(
                ballooning, self.rib1.profile_3d.data, self.rib2.profile_3d.data
        )):
            l = norm(right_point - left_point)  # L
            lnew = sum([norm(c.prof1.data[index] - c.prof2.data[index]) for c in cells])  # L-NEW
            for c in cells:
                newval = lnew / l / bl if bl != 0 else 1
                if newval < 1.:
                    c.ballooning_phi.append(Ballooning.arcsinc(newval))  # B/L NEW 1 / (bl * l / lnew)
                else:
                    #c.ballooning_phi.append(Ballooning.arcsinc(1.))
                    c.ballooning_phi.append(0.)
                    #raise ValueError("mull")
        return cells

    @property
    def ribs(self):
        return [self.rib1, self.rib2]

    @property
    def _yvalues(self):
        return [0] + [mrib.y_value for mrib in self._miniribs] + [1]

    @property
    def x_values(self):
        return consistent_value(self.ribs, 'profile_2d.x_values')

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
            return self.basic_cell.midrib(y, ballooning=ballooning)
        if ballooning:
            i = 0
            while self._yvalues[i + 1] < y:
                i += 1
            cell = self._child_cells[i]
            y_new = (y - self._yvalues[i]) / (self._yvalues[i + 1] - self._yvalues[i])
            return cell.midrib(y_new, arc_argument=arc_argument)
        else:
            return self.basic_cell.midrib(y, ballooning=False)

    @cached_property('ballooning', 'rib1.profile_2d.numpoints', 'rib2.profile_2d.numpoints')
    def ballooning_phi(self):
        x_values = self.rib1.profile_2d.x_values
        balloon = [self.ballooning[i] for i in x_values]
        return HashedList([Ballooning.arcsinc(1. / (1+bal)) if bal > 0 else 0 for bal in balloon])

    @property
    def ribs(self):
        return [self.rib1, self.rib2]

    @property
    def span(self):
        return norm((self.rib1.pos - self.rib2.pos) * [0, 1, 1])

    @property
    def area(self):
        p1_1 = self.rib1.align([0, 0, 0])
        p1_2 = self.rib1.align([1, 0, 0])
        p2_1 = self.rib2.align([0, 0, 0])
        p2_2 = self.rib2.align([1, 0, 0])
        return 0.5 * (norm(numpy.cross(p1_2 - p1_1, p2_1 - p1_1)) + norm(numpy.cross(p2_2 - p2_1, p2_2 - p1_2)))

    @property
    def projected_area(self):
        """ return the z component of the crossproduct 
            of the cell diagonals"""
        p1_1 = numpy.array(self.rib1.align([0, 0, 0]))
        p1_2 = numpy.array(self.rib1.align([1, 0, 0]))
        p2_1 = numpy.array(self.rib2.align([0, 0, 0]))
        p2_2 = numpy.array(self.rib2.align([1, 0, 0]))
        return -0.5 * numpy.cross(p2_1 - p1_2, p2_2 - p1_1)[-1]  

    @property
    def aspect_ratio(self):
        return self.span ** 2 / self.area

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self):
        self.rib2, self.rib1 = self.rib1, self.rib2
        for rib in self.ribs:
            rib.mirror()

    def average_rib(self, num_midribs=8):
        average_rib = self.midrib(0).flatten().normalize()
        for y in numpy.linspace(0, 1, num_midribs)[1:]:
            average_rib += self.midrib(y).flatten().normalize()
        return average_rib * (1. / num_midribs)
