from __future__ import division
import copy
import logging
import math
from typing import Callable, List

import numpy as np
from openglider.airfoil.profile_2d import Profile2D
import openglider.vector
import openglider.utils
from openglider.airfoil import Profile3D
from openglider.glider.ballooning import Ballooning
from openglider.glider.cell import BasicCell
from openglider.glider.cell.elements import Panel
from openglider.mesh import Mesh, Polygon, Vertex
from openglider.utils import consistent_value, linspace
from openglider.utils.cache import (
    CachedObject,
    HashedList,
    cached_function,
    cached_property, hash_list,
)
from openglider.vector import norm, normalize
from openglider_cpp import euklid

logging.getLogger(__file__)

class Cell(CachedObject):
    diagonal_naming_scheme = "{cell.name}d{diagonal_no}"
    strap_naming_scheme = "{cell.name}s{strap_no}"
    panel_naming_scheme = "{cell.name}p{panel_no}"
    panel_naming_scheme_upper = "{cell.name}pu{panel_no}"
    panel_naming_scheme_lower = "{cell.name}pl{panel_no}"
    minirib_naming_scheme = "{cell.name}mr{minirib_no}"

    sigma_3d_cut = 0.04

    def __init__(self, rib1, rib2, ballooning, miniribs=None, panels: List["Panel"]=None,
                 diagonals: list=None, straps: list=None, rigidfoils: list=None, name="unnamed", **kwargs):
        self.rib1 = rib1
        self.rib2 = rib2
        self.miniribs = miniribs or []
        self.diagonals = diagonals or []
        self.straps = straps or []
        self.ballooning = ballooning
        self.panels = panels or []
        self.rigidfoils = rigidfoils or []
        self.name = name

        for kwarg, value in kwargs.items():
            setattr(self, kwarg, value)

    def __json__(self):
        return {"rib1": self.rib1,
                "rib2": self.rib2,
                "ballooning": self.ballooning,
                "miniribs": self.miniribs,
                "diagonals": self.diagonals,
                "panels": self.panels,
                "straps": self.straps,
                "rigidfoils": self.rigidfoils,
                "name": self.name,
                "sigma_3d_cut": self.sigma_3d_cut
                }
    
    def __hash__(self) -> int:
        return hash_list(self.rib1, self.rib2, *self.miniribs, *self.diagonals)

    def rename_panels(self, seperate_upper_lower=False):
        if seperate_upper_lower:
            upper = [panel for panel in self.panels if panel.mean_x < 0]
            lower = [panel for panel in self.panels if panel.mean_x >= 0]
            sort_func = lambda panel: abs(panel.mean_x())
            upper.sort(key=sort_func)
            lower.sort(key=sort_func)

            for panel_no, panel in enumerate(upper):
                panel.name = self.panel_naming_scheme_upper.format(cell=self, panel_no=panel_no+1)
            for panel_no, panel in enumerate(lower):
                panel.name = self.panel_naming_scheme_lower.format(cell=self, panel_no=panel_no+1)

        else:
            self.panels.sort(key=lambda panel: panel.mean_x())
            for panel_no, panel in enumerate(self.panels):
                panel.name = self.panel_naming_scheme.format(cell=self, panel=panel, panel_no=panel_no+1)

    def rename_parts(self, seperate_upper_lower=False):
        for diagonal_no, diagonal in enumerate(self.diagonals):
            diagonal.name = self.diagonal_naming_scheme.format(cell=self, diagonal=diagonal, diagonal_no=diagonal_no+1)

        for strap_no, strap in enumerate(self.straps):
            strap.name = self.strap_naming_scheme.format(cell=self, strap=strap, strap_no=strap_no+1)

        for minirib_no, minirib in enumerate(self.miniribs):
            minirib.name = self.minirib_naming_scheme.format(cell=self, minirib=minirib, minirib_no=minirib_no+1)

        self.rename_panels(seperate_upper_lower=seperate_upper_lower)

    @cached_property('rib1.profile_3d', 'rib2.profile_3d', 'ballooning_phi')
    def basic_cell(self) -> BasicCell:
        return BasicCell(self.rib1.profile_3d, self.rib2.profile_3d, self.ballooning_phi)

    def get_normvector(self):
        p1 = self.rib1.point(-1)
        p2 = self.rib2.point(0)

        p4 = self.rib1.point(0)
        p3 = self.rib2.point(-1)

        return normalize(np.cross(p1-p2, p3-p4))

    @cached_property('miniribs', 'rib1', 'rib2')
    def rib_profiles_3d(self) -> list:
        """
        Get all the ribs 3d-profiles, including miniribs
        """
        profiles = [self.rib1.profile_3d]
        profiles += [self._make_profile3d_from_minirib(mrib) for mrib in self.miniribs]
        profiles += [self.rib2.profile_3d]

        return profiles

    def get_connected_panels(self, skip=None):
        panels = []
        self.panels.sort(key=lambda panel: panel.mean_x())

        p0 = self.panels[0]
        for p in self.panels[1:]:
            if p.cut_front["type"] != skip and  p.cut_front == p0.cut_back:
                p0 = Panel(p0.cut_front, p.cut_back, material_code=p0.material_code)
            else:
                panels.append(p0)
                p0 = p

        panels.append(p0)
        return panels

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
    def x_values(self) -> list:
        return consistent_value(self.ribs, 'profile_2d.x_values')

    @property
    def prof1(self):
        return self.rib1.profile_3d

    @property
    def prof2(self):
        return self.rib2.profile_3d

    def point(self, y=0, i=0, k=0):
        return self.midrib(y).point(i, k)

    @cached_function("self")
    def midrib(self, y, ballooning=True, arc_argument=True, with_numpy=True, close_trailing_edge=False):
        kwargs = {
            "ballooning": ballooning,
            "arc_argument": arc_argument,
            "with_numpy": with_numpy,
            "close_trailing_edge": close_trailing_edge
        }
        if len(self._child_cells) == 1:
            return self.basic_cell.midrib(y, **kwargs)
        if ballooning:
            i = 0
            while self._yvalues[i + 1] < y:
                i += 1
            cell = self._child_cells[i]
            y_new = (y - self._yvalues[i]) / (self._yvalues[i + 1] - self._yvalues[i])
            return cell.midrib(y_new, **kwargs)
        else:
            return self.basic_cell.midrib(y, ballooning=False)

    def get_midribs(self, numribs):
        y_values = linspace(0, 1, numribs)
        return [self.midrib(y) for y in y_values]

    def get_spline(self, numribs, u_poles=20, v_poles=4, u_degree=3, v_degree=3):
        try:
            import nurbs
        except ImportError:
            logging.error("noorbs library not available")
            return None


        r1 = self.rib1
        assert v_poles < numribs
        assert u_poles < len(r1.profile_2d)

        u_space = r1.profile_2d.get_length_parameter(scale=0)
        v_space = np.linspace(0, 1, numribs)
        grid = self.get_midribs(numribs)
        uv_list = []
        x_list = []
        for ui, u in enumerate(u_space):
            for vi, v in enumerate(v_space):
                uv_list.append([u, v])
                x_list.append(grid[vi][ui])
        uv = np.array(uv_list)
        x = np.array(x_list)

        # create base with nurbs
        u_knots = nurbs.create_knots_vector(u_min=0, u_max=1, degree=u_degree, num_poles=u_poles)
        v_knots = nurbs.create_knots_vector(u_min=0, u_max=1, degree=v_degree, num_poles=v_poles)
        weights = np.ones((u_poles * v_poles))
        base = nurbs.NurbsBase2D(u_knots, v_knots, weights, u_degree, v_degree)
        mat = base.getInfluenceMatrix(uv).toarray()
        # min (mat @ poles - x) ** 2
        assert v_poles < numribs
        poles = np.linalg.lstsq(mat, x)[0]
        return u_poles, v_poles, u_knots, v_knots, u_degree, v_degree, poles, weights


    @cached_property('ballooning', 'rib1.profile_2d.numpoints', 'rib2.profile_2d.numpoints')
    def ballooning_phi(self):
        x_values = self.rib1.profile_2d.x_values
        balloon = [self.ballooning[i] for i in x_values]
        return HashedList([Ballooning.arcsinc(1. / (1+bal)) if bal > 0 else 0 for bal in balloon])

    @property
    def span(self):
        return norm((self.rib1.pos - self.rib2.pos) * [0, 1, 1])

    @property
    def area(self):
        p1_1 = self.rib1.align([0, 0, 0])
        p1_2 = self.rib1.align([1, 0, 0])
        p2_1 = self.rib2.align([0, 0, 0])
        p2_2 = self.rib2.align([1, 0, 0])
        return 0.5 * (norm(np.cross(p1_2 - p1_1, p2_1 - p1_1)) + norm(np.cross(p2_2 - p2_1, p2_2 - p1_2)))

    @property
    def projected_area(self):
        """ return the z component of the crossproduct
            of the cell diagonals"""
        p1_1 = np.array(self.rib1.align([0, 0, 0]))
        p1_2 = np.array(self.rib1.align([1, 0, 0]))
        p2_1 = np.array(self.rib2.align([0, 0, 0]))
        p2_2 = np.array(self.rib2.align([1, 0, 0]))
        return -0.5 * np.cross(p2_1 - p1_2, p2_2 - p1_1)[-1]

    @property
    def centroid(self):
        p1_1 = np.array(self.rib1.align([0, 0, 0]))
        p1_2 = np.array(self.rib1.align([1, 0, 0]))
        p2_1 = np.array(self.rib2.align([0, 0, 0]))
        p2_2 = np.array(self.rib2.align([1, 0, 0]))

        centroid = (p1_1 + p1_2 + p2_1 + p2_2) / 4
        return centroid

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

    def mean_rib(self, num_midribs=8) -> Profile2D:
        mean_rib = self.midrib(0).flatten().normalize()
        for y in np.linspace(0, 1, num_midribs)[1:]:
            mean_rib += self.midrib(y).flatten().normalize()
        return mean_rib * (1. / num_midribs)

    def get_mesh_grid(self, numribs=0, with_numpy=False, half_cell=False):
        """
        Get Cell-grid
        :param numribs: number of miniribs to calculate
        :return: grid
        """
        numribs += 1

        grid = []
        rib_indices = range(numribs + 1)
        if half_cell:
            rib_indices = rib_indices[(numribs) // 2:]
        for rib_no in rib_indices:
            y = rib_no / max(numribs, 1)
            rib = self.midrib(y, with_numpy=with_numpy).data
            grid.append(Vertex.from_vertices_list(rib[:-1]))
        return grid

    def get_mesh(self, numribs=0, with_numpy=False, half_cell=False):
        """
        Get Cell-mesh
        :param numribs: number of miniribs to calculate
        :return: mesh
        """

        grid = self.get_mesh_grid(numribs=numribs,
                                  with_numpy=with_numpy,
                                  half_cell=half_cell)

        trailing_edge = []

        quads = []
        for rib_left, rib_right in zip(grid[:-1], grid[1:]):
            numpoints = len(rib_left)
            for i in range(numpoints):
                i_next = (i+1)%numpoints
                pol = Polygon([
                    rib_left[i],
                    rib_right[i],
                    rib_right[i_next],
                    rib_left[i_next]])

                quads.append(pol)
        for rib in grid:
            trailing_edge.append(rib[0])
        mesh = Mesh({"hull": quads}, 
                    {self.rib1.name: grid[0], self.rib2.name: grid[-1], "trailing_edge": trailing_edge})
        return mesh

    def get_mesh_mapping_grid(self, cell_number=0, numribs=0, with_numpy=False, half_cell=False):
        """
        Get Cell-grid
        :cell_number: number of cell
        :param numribs: number of miniribs to calculate
        :return: mesh
        """
        numribs += 1

        grid = []
        rib_indices = range(numribs + 1)
        if half_cell:
            rib_indices = rib_indices[(numribs) // 2:]
        for rib_no in rib_indices:
            y = rib_no / max(numribs, 1)
            rib = (self.rib1.profile_2d.get_data(negative_x=True) * (1 - y) + 
                   self.rib2.profile_2d.get_data(negative_x=True) * y)
            y += cell_number
            rib = np.array([rib.T[0], np.array([y]*len(rib)), rib.T[1]]).T  # insert y-value
            grid.append(Vertex.from_vertices_list(rib))
        return grid

    def get_mesh_mapping(self, cell_number=0, numribs=0, with_numpy=False, half_cell=False):
        """
        Get Cell-mesh
        :cell_number: number of cell
        :param numribs: number of miniribs to calculate
        :return: mesh
        """

        grid = self.get_mesh_mapping_grid(cell_number=cell_number, 
                                          numribs=numribs,
                                          with_numpy=with_numpy,
                                          half_cell=half_cell)     

        quads = []
        for rib_left, rib_right in zip(grid[:-1], grid[1:]):
            numpoints = len(rib_left)
            for i in range(numpoints - 1):
                i_next = i+1
                pol = Polygon([rib_left[i], rib_right[i], rib_right[i_next], rib_left[i_next]])
                quads.append(pol)
        mesh = Mesh({"hull": quads}, 
                    {self.rib1.name: grid[0], self.rib2.name: grid[-1]})
        return mesh

    @cached_function("self")
    def get_flattened_cell(self, numribs=50):
        midribs = self.get_midribs(numribs)
        numpoints = len(midribs[0])

        len_dct = {}
        def get_length(ik1, ik2):
            index_str = f"{ik1}:{ik2}"
            if index_str not in len_dct:
                points = []
                for i, rib in enumerate(midribs):
                    x = ik1 + i/(numribs-1) * (ik2-ik1)
                    points.append(rib[x])
                
                line = euklid.PolyLine3D(points)

                len_dct[index_str] = line.get_length()

            return len_dct[index_str]

        l_0 = get_length(0, 0)

        left_bal = [np.array([0, 0])]
        right_bal = [np.array([l_0, 0])]

        def get_point(p1, p2, l_0, l_l, l_r, left=True):
            lx = (l_0**2 + l_l**2 - l_r**2) / (2*l_0)
            ly_sq = l_l**2 - lx**2
            if ly_sq > 0:
                ly = math.sqrt(ly_sq)
            else:
                ly = 0
            diff = openglider.vector.normalize(p2 - p1)
            if left:
                diff_y = diff.dot([[0, 1], [-1, 0]])
            else:
                diff_y = diff.dot([[0, -1], [1, 0]])

            return p1 + lx * diff + ly * diff_y


        for i in range(numpoints-1):
            p1 = left_bal[-1]
            p2 = right_bal[-1]


            d_l = openglider.vector.norm(midribs[0][i] - midribs[0][i+1])
            d_r = openglider.vector.norm(midribs[-1][i] - midribs[-1][i+1])
            l_0 = get_length(i, i)

            if False:
                pl_2 = get_point(p1, p2, l_0, d_l, get_length(i+1, i))
                pr_2 = get_point(p2, pl_2, get_length(i+1, i), d_r, get_length(i+1, i+1), left=False)
            else:
                pr_2 = get_point(p2, p1, l_0, d_r, get_length(i, i+1), left=False)
                pl_2 = get_point(p1, pr_2, get_length(i, i+1), d_l, get_length(i+1, i+1))

            left_bal.append(pl_2)
            right_bal.append(pr_2)
            #right_bal.append(get_point(p2, p1, l_0, d_r, get_length(i, i+1), left=False))

        ballooned = [
            euklid.PolyLine2D(left_bal),
            euklid.PolyLine2D(right_bal)
        ]

        inner = []
        for x in openglider.utils.linspace(0, 1, numribs + 2):
            inner.append(ballooned[0].mix(ballooned[1], x))

        #ballooned = [left_bal, right_bal]

        return {
            "inner": inner,
            "ballooned": ballooned
            }
    
    def calculate_3d_shaping(self, panels=None, numribs=10):
        if panels is None:
            panels = self.panels

        flat = self.get_flattened_cell(numribs)
        inner = flat["inner"]

        cuts_3d = {}

        def cut_hash(cut):
            return "{}-{}-{}".format(cut["left"], cut["right"], cut["type"])

        def add_amount(cut, amount):
            cut_key = cut_hash(cut)

            for key in cuts_3d:
                if key == cut_key:
                    old = cuts_3d[key]

                    cuts_3d[key] = [(x1+x2)/2 for x1, x2 in zip(old, amount)]
                    return

            cuts_3d[cut_key] = amount

        def get_amount(cut):
            cut_key = cut_hash(cut)
            data = cuts_3d[cut_key]
            # TODO: Investigate
            return [max(0, x) for x in data]

        for panel in panels:
            amount_front, amount_back = panel.integrate_3d_shaping(self, self.sigma_3d_cut, inner)

            add_amount(panel.cut_front, amount_front)
            add_amount(panel.cut_back, amount_back)

        cut_3d_types = ["cut_3d"]
        for panel in panels:
            if panel.cut_front["type"] in cut_3d_types:
                panel.cut_front["amount_3d"] = get_amount(panel.cut_front)
            else:
                panel.cut_front["amount_3d"] = [0] * (numribs+2)
            if panel.cut_back["type"] in cut_3d_types:
                panel.cut_back["amount_3d"] = get_amount(panel.cut_back)
            else:
                panel.cut_back["amount_3d"] = [0] * (numribs+2)

