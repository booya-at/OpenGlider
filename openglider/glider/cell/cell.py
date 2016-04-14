from __future__ import division
import copy
import numpy

from openglider.airfoil import Profile3D
from openglider.glider.ballooning import Ballooning
from openglider.glider.cell import BasicCell
from openglider.utils import consistent_value, linspace
from openglider.utils.cache import CachedObject, cached_property, HashedList
from openglider.vector import norm
from openglider.mesh import Mesh


class Cell(CachedObject):
    diagonal_naming_scheme = "{cell.name}d{diagonal_no}"
    strap_naming_scheme = "{cell.name}s{strap_no}"
    panel_naming_scheme = "{cell.name}p{panel_no}"
    minirib_naming_scheme = "{cell.name}mr{minirib_no}"

    def __init__(self, rib1, rib2, ballooning, miniribs=None, panels=None,
                 diagonals=None, straps=None, name="unnamed"):
        self.rib1 = rib1
        self.rib2 = rib2
        self.miniribs = miniribs or []
        self.diagonals = diagonals or []
        self.straps = straps or []
        self.ballooning = ballooning
        self.panels = panels or []
        self.name = name

    def __json__(self):
        return {"rib1": self.rib1,
                "rib2": self.rib2,
                "ballooning": self.ballooning,
                "miniribs": self.miniribs,
                "diagonals": self.diagonals,
                "panels": self.panels,
                "straps": self.straps}

    def rename_parts(self):
        for diagonal_no, diagonal in enumerate(self.diagonals):
            diagonal.name = self.diagonal_naming_scheme.format(cell=self, diagonal=diagonal, diagonal_no=diagonal_no)

        for strap_no, strap in enumerate(self.straps):
            strap.name = self.strap_naming_scheme.format(cell=self, strap=strap, strap_no=strap_no)

        for panel_no, panel in enumerate(self.panels):
            panel.name = self.panel_naming_scheme.format(cell=self, panel=panel, panel_no=panel_no)

        for minirib_no, minirib in enumerate(self.miniribs):
            minirib.name = self.minirib_naming_scheme.format(cell=self, minirib=minirib, minirib_no=minirib_no)

    @cached_property('rib1.profile_3d', 'rib2.profile_3d', 'ballooning_phi')
    def basic_cell(self):
        return BasicCell(self.rib1.profile_3d, self.rib2.profile_3d, self.ballooning_phi)

    @cached_property('miniribs', 'rib1', 'rib2')
    def rib_profiles_3d(self):
        """
        Get all the ribs 3d-profiles, including miniribs
        """
        profiles = [self.rib1.profile_3d]
        profiles += [self._make_profile3d_from_minirib(mrib) for mrib in self.miniribs]
        profiles += [self.rib2.profile_3d]

        return profiles

    def _make_profile3d_from_minirib(self, minirib):
        # self.basic_cell.prof1 = self.prof1
        # self.basic_cell.prof2 = self.prof2
        shape_with_ballooning = self.basic_cell.midrib(minirib.y_value,
                                                       True).data
        shape_without_ballooning = self.basic_cell.midrib(minirib.y_value,
                                                          False).data
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
        if not self.miniribs:
            return cells

        for index, xvalue in enumerate(self.x_values):
            left_point = self.rib1.profile_3d.data[index]
            right_point = self.rib2.profile_3d.data[index]
            bl = self.ballooning[xvalue]

            l = norm(right_point - left_point)  # L
            lnew = sum([norm(c.prof1.data[index] - c.prof2.data[index]) for c in cells])  # L-NEW

            for c in cells:
                if bl > 0:
                    newval = l / lnew * (bl+1/2) - 1/2
                    #newval = l/lnew / bl
                    #newval = lnew / l / bl if bl != 0 else 1
                    c.ballooning_phi.append(Ballooning.arcsinc(1/(1+newval)))  # B/L NEW 1 / (bl * l / lnew)
                else:
                    c.ballooning_phi.append(0.)
        return cells

    @property
    def ribs(self):
        return [self.rib1, self.rib2]

    @property
    def _yvalues(self):
        return [0] + [mrib.y_value for mrib in self.miniribs] + [1]

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

    def midrib(self, y, ballooning=True, arc_argument=False, with_numpy=False):
        if len(self._child_cells) == 1:
            return self.basic_cell.midrib(y, ballooning=ballooning)
        if ballooning:
            i = 0
            while self._yvalues[i + 1] < y:
                i += 1
            cell = self._child_cells[i]
            y_new = (y - self._yvalues[i]) / (self._yvalues[i + 1] - self._yvalues[i])
            return cell.midrib(y_new, arc_argument=arc_argument, with_numpy=with_numpy)
        else:
            return self.basic_cell.midrib(y, ballooning=False)

    def get_midribs(self, numribs):
        y_values = linspace(0, 1, numribs)
        return [self.midrib(y) for y in y_values]

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

    def mirror(self, mirror_ribs=True):
        self.rib2, self.rib1 = self.rib1, self.rib2

        if mirror_ribs:
            for rib in self.ribs:
                rib.mirror()

        for diagonal in self.diagonals:
            diagonal.mirror()

        for strap in self.straps:
            strap.mirror()

        for panel in self.panels:
            panel.mirror()

    def mean_rib(self, num_midribs=8):
        mean_rib = self.midrib(0).flatten().normalize()
        for y in numpy.linspace(0, 1, num_midribs)[1:]:
            mean_rib += self.midrib(y).flatten().normalize()
        return mean_rib * (1. / num_midribs)

    def get_mesh(self,  numribs=0, with_numpy=False):
        """
        Get Cell-mesh
        :param numribs: number of miniribs to calculate
        :return: mesh
        """
        numribs += 1
        # TODO: doesnt work for numribs=0?
        xvalues = self.rib1.profile_2d.x_values
        ribs = []
        points = []
        nums = []
        count = 0
        for rib_no in range(numribs + 1):
            y = rib_no / max(numribs, 1)
            midrib = self.midrib(y, with_numpy=with_numpy).data[:-1]
            points += list(midrib)
            nums.append([i + count for i, _ in enumerate(midrib)])
            count += len(nums[-1])
            nums[-1].append(nums[-1][0])
            
        quads = []
        for rib_no, _ in enumerate(nums[:-1]):
            num_l = nums[rib_no]
            num_r = nums[rib_no + 1]
            for i, _ in enumerate(num_l[:-1]):
                quads.append([
                    num_l[i],
                    num_r[i],             
                    num_r[i + 1],
                    num_l[i + 1]])

        connection_info = {self.rib1: numpy.array(nums[0][:-1], int), 
                           self.rib2: numpy.array(nums[-1][:-1], int)}            
        return Mesh(numpy.array(points), quads, connection_info)