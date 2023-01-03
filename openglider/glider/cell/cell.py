from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Sequence, Tuple

import euklid
import openglider.utils
import openglider.vector
import pyfoil
from openglider.airfoil import Profile3D
from openglider.glider.ballooning.base import BallooningBase
from openglider.glider.cell.attachment_point import CellAttachmentPoint
from openglider.glider.cell.basic_cell import BasicCell
from openglider.glider.cell.diagonals import DiagonalRib, TensionStrap
from openglider.glider.cell.panel import PANELCUT_TYPES, Panel, PanelCut
from openglider.glider.cell.rigidfoil import PanelRigidFoil
from openglider.glider.rib import MiniRib, Rib
from openglider.mesh import Mesh, Polygon, Vertex
from openglider.utils import consistent_value, linspace
from openglider.utils.cache import (HashedList, cached_function,
                                    cached_property, hash_list)
from openglider.utils.dataclass import BaseModel, Field

logger = logging.getLogger(__file__)


class FlattenedCell(BaseModel):
    inner: List[euklid.vector.PolyLine2D]
    ballooned: Tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]


class Cell(BaseModel):
    rib1: Rib
    rib2: Rib
    ballooning: BallooningBase
    attachment_points: List[CellAttachmentPoint] = Field(default_factory=list)
    miniribs: List[MiniRib] = Field(default_factory=list)
    panels: List[Panel] = Field(default_factory=list)
    diagonals: List[DiagonalRib] = Field(default_factory=list)
    straps: List[TensionStrap] = Field(default_factory=list)
    rigidfoils: List[PanelRigidFoil] = Field(default_factory=list)
    name: str = "unnamed"

    ballooning_ramp: float | None = None
    sigma_3d_cut: float = 0.06

    diagonal_naming_scheme = "{cell.name}d{diagonal_no}"
    strap_naming_scheme = "{cell.name}s{side}{diagonal_no}"
    panel_naming_scheme = "{cell.name}p{panel_no}"
    panel_naming_scheme_upper = "{cell.name}pu{panel_no}"
    panel_naming_scheme_lower = "{cell.name}pl{panel_no}"
    minirib_naming_scheme = "{cell.name}mr{minirib_no}"
    
    def __hash__(self) -> int:
        return hash_list(self.rib1, self.rib2, *self.miniribs, *self.diagonals)

    def rename_panels(self, cell_no: int, seperate_upper_lower: bool=True) -> None:
        if seperate_upper_lower:
            upper = [panel for panel in self.panels if not panel.is_lower()]
            lower = [panel for panel in self.panels if panel.is_lower()]
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
    
    def rename_diagonals(self, diagonals: Sequence[DiagonalRib | TensionStrap], cell_no: int, naming_scheme: str) -> None:
        upper = []
        lower = []

        for diagonal in diagonals:
            if diagonal.get_average_x() > 0:
                lower.append(diagonal)
            else:
                upper.append(diagonal)
        
        lower.sort(key=lambda d: d.get_average_x())
        upper.sort(key=lambda d: -d.get_average_x())

        for i, d in enumerate(lower):
            d.name = naming_scheme.format(cell=self, cell_no=cell_no, diagonal=d, diagonal_no=i+1, side="l")

        for i, d in enumerate(upper):
            d.name = naming_scheme.format(cell=self, cell_no=cell_no, diagonal=d, diagonal_no=i+1, side="u")



    def rename_parts(self, cell_no: int, seperate_upper_lower: bool=False) -> None:
        self.rename_diagonals(self.diagonals, cell_no, self.diagonal_naming_scheme)
        self.rename_diagonals(self.straps, cell_no, self.strap_naming_scheme)

        for minirib_no, minirib in enumerate(self.miniribs):
            minirib.name = self.minirib_naming_scheme.format(cell=self, minirib=minirib, minirib_no=minirib_no+1)

        self.rename_panels(cell_no, seperate_upper_lower=seperate_upper_lower)

    @cached_property('rib1', 'rib2', 'ballooning_phi')
    def basic_cell(self) -> BasicCell:
        profile1 = self.rib1.profile_3d
        profile2 = self.rib2.profile_3d

        profile_numpoints = self.rib1.profile_2d.numpoints
        profile_x_values = self.rib1.profile_2d.x_values

        if self.rib2.profile_2d.numpoints != profile_numpoints:
            raise ValueError(f"numpoints not matching {self.name}: {profile_numpoints}, {self.rib2.profile_2d.numpoints}")

        if len(profile1) != profile_numpoints:
            profile1 = self.rib1.get_profile_3d(x_values=profile_x_values)
        if len(profile2) != profile_numpoints:
            profile2 = self.rib2.get_profile_3d(x_values=profile_x_values)
        
        return BasicCell(profile1, profile2, self.ballooning_phi)

    def get_normvector(self) -> euklid.vector.Vector3D:
        p1 = self.rib1.point(-1)
        p2 = self.rib2.point(0)

        p4 = self.rib1.point(0)
        p3 = self.rib2.point(-1)

        return (p1-p2).cross(p3-p4).normalized()

    @cached_property('miniribs', 'rib1', 'rib2')
    def rib_profiles_3d(self) -> list:
        """
        Get all the ribs 3d-profiles, including miniribs
        """
        profiles = [self.rib1.profile_3d]
        profiles += [self._make_profile3d_from_minirib(mrib) for mrib in self.miniribs]
        profiles += [self.rib2.profile_3d]

        return profiles

    def get_connected_panels(self, skip: Optional[PANELCUT_TYPES]=None) -> List[Panel]:
        panels = []
        self.panels.sort(key=lambda panel: panel.mean_x())

        p0 = self.panels[0]
        for p in self.panels[1:]:
            if p.cut_front.cut_type != skip and  p.cut_front == p0.cut_back:
                p0 = Panel(p0.cut_front, p.cut_back, material=p0.material)
            else:
                panels.append(p0)
                p0 = p

        panels.append(p0)
        return panels

    def _make_profile3d_from_minirib(self, minirib: MiniRib) -> Profile3D:
        # self.basic_cell.prof1 = self.prof1
        # self.basic_cell.prof2 = self.prof2
        shape_with_ballooning = self.basic_cell.midrib(minirib.yvalue, ballooning=True, arc_argument=False).curve.nodes
        shape_without_ballooning = self.basic_cell.midrib(minirib.yvalue, ballooning=False).curve.nodes
        points: List[euklid.vector.Vector3D] = []
        for xval, with_bal, without_bal in zip(
                self.x_values, shape_with_ballooning, shape_without_ballooning):
            fakt = minirib.multiplier(xval)  # factor ballooned/unb. (0-1)
            point = without_bal + (with_bal - without_bal) * fakt
            points.append(point)
        return Profile3D(euklid.vector.PolyLine3D(points))

    @cached_property('rib_profiles_3d')
    def _child_cells(self) -> List[BasicCell]:
        """
        get all the sub-cells within the current cell,
        (separated by miniribs)
        """
        # TODO: test / fix
        cells: List[BasicCell] = []
        for cell_no in range(len(self.rib_profiles_3d)-1):
            leftrib = self.rib_profiles_3d[cell_no]
            rightrib = self.rib_profiles_3d[cell_no+1]
            cells.append(BasicCell(leftrib, rightrib, ballooning=[], name=f"{self.name}_{cell_no}"))
        if not self.miniribs:
            return cells
        
        cell_phi = self.basic_cell.ballooning_phi
        profile_phi = []

        for index in range(len(self.x_values)):
            phi_values = [0]
            for mrib in self.miniribs:
                phi = cell_phi[index] + math.asin((2 * mrib.yvalue - 1) * math.sin(cell_phi[index]))
                phi_values.append(phi)
            phi_values.append(2*cell_phi[index])

            profile_phi.append(phi_values)

        for index, xvalue in enumerate(self.x_values):
            left_point = self.rib1.profile_3d.curve.nodes[index]
            right_point = self.rib2.profile_3d.curve.nodes[index]

            phi_values = profile_phi[index]
            phi_max = max(phi_values)

            bl = self.ballooning_modified[xvalue]

            length_bow = (1+bl) * (right_point - left_point).length()  # L

            #lnew = sum([(c.prof1.curve.nodes[index] - c.prof2.curve.nodes[index]).length() for c in cells])  # L-NEW

            for cell_no, cell in enumerate(cells):
                if bl > 0:
                    phi2= (phi_values[cell_no+1] - phi_values[cell_no]) / phi_max
                    length_bow_part = length_bow * phi2
                    lnew = (cell.prof1.curve.nodes[index] - cell.prof2.curve.nodes[index]).length()
                    
                    ballooning_new = (length_bow_part/lnew) - 1

                    #print(index, cell_no, phi2, phi_values, phi_max, length_bow_part, lnew, ballooning_new)

                    if ballooning_new < 0:
                        raise ValueError(f"invalid ballooning for subcell: {self.name} / {cell_no}")
                        ballooning_new = 0
                        #print("JO")

                    cell.ballooning_phi.append(BallooningBase.arcsinc(1/(1+ballooning_new)))  # B/L NEW 1 / (bl * l / lnew)
                else:
                    cell.ballooning_phi.append(0.)
        return cells

    @property
    def ribs(self) -> List[Rib]:
        return [self.rib1, self.rib2]

    @property
    def _yvalues(self) -> List[float]:
        return [0.] + [mrib.yvalue for mrib in self.miniribs] + [1.]

    @property
    def x_values(self) -> List[float]:
        return consistent_value(self.ribs, 'profile_2d.x_values')

    @property
    def prof1(self) -> openglider.airfoil.Profile3D:
        return self.rib1.profile_3d

    @property
    def prof2(self) -> openglider.airfoil.Profile3D:
        return self.rib2.profile_3d

    def point(self, y: float=0, i: int=0, k: float=0.) -> euklid.vector.Vector3D:
        return self.midrib(y).get(i+k)

    @cached_function("self")
    def midrib(self, y: float, ballooning: bool=True, arc_argument: bool=True, close_trailing_edge: bool=False) -> Profile3D:
        kwargs = {
            "ballooning": ballooning,
            "arc_argument": arc_argument,
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

    def get_midribs(self, numribs: int) -> List[Profile3D]:
        y_values = linspace(0, 1, numribs)
        return [self.midrib(y) for y in y_values]
    
    @cached_property('ballooning', 'rib1.profile_2d.x_values', 'rib2.profile_2d.x_values', 'panels')
    def ballooning_modified(self) -> BallooningBase:
        if self.ballooning_ramp is None:
            return self.ballooning

        panels = self.get_connected_panels()
        cuts = set()

        for p in panels:
            x1 = max([p.cut_front.x_left, p.cut_front.x_right])
            x2 = min([p.cut_back.x_left, p.cut_back.x_right])

            for x in (x1, x2):
                if abs(x) < (1 - 1e-10):
                    cuts.add(x)
        
        ballooning = self.ballooning
        from openglider.glider.ballooning.new import BallooningNew
        for cut in cuts:
            def y(x: euklid.vector.Vector2D) -> euklid.vector.Vector2D:
                distance = abs(x[0]-cut)
                y_new = x[1]

                if distance <= self.ballooning_ramp:
                    y_new *= -(math.cos(distance / self.ballooning_ramp * math.pi) - 1) / 2
                
                    return euklid.vector.Vector2D([x[0], y_new])
                
                return x

            ballooning = BallooningNew(euklid.vector.Interpolation([y(x) for x in ballooning]), ballooning.name)
        
        return ballooning

    @cached_property('ballooning_modified')
    def ballooning_phi(self) -> HashedList:
        x_values = [max(-1, min(1, x)) for x in self.rib1.profile_2d.x_values]
        balloon = [self.ballooning_modified[i] for i in x_values]
        return HashedList([BallooningBase.arcsinc(1. / (1+bal)) if bal > 0 else 0 for bal in balloon])
    
    @cached_property('ballooning', '_child_cells')
    def ballooning_tension_factors(self) -> List[float]:
        if len(self._child_cells) <= 1:
            return self.basic_cell.ballooning_tension_factors
        
        child_factors = [cell.ballooning_tension_factors for cell in self._child_cells]

        factors: List[float] = []

        prof1 = self.prof1.curve
        prof2 = self.prof2.curve

        for i in range(len(prof1.nodes)):
            tension = 0.
            diff = (prof1.nodes[i] - prof2.nodes[i]).normalized()

            for cell, cell_factors in zip(self._child_cells, child_factors):
                diff_child = (cell.prof1.curve.nodes[i] - cell.prof2.curve.nodes[i])
                cos_psi = abs(diff.dot(diff_child.normalized()))
                _tension = cell_factors[i]

                if cos_psi > 1e-5 and cos_psi < 1:
                    _tension = cell_factors[i]*cos_psi - math.sqrt(1-cos_psi**2)*diff_child.length()/2

                tension = max(tension, _tension)
            
            factors.append(tension)
        
        return factors


    @property
    def span(self) -> float:
        return ((self.rib1.pos - self.rib2.pos) * euklid.vector.Vector3D([0, 1, 1])).length()

    @property
    def area(self) -> float:
        p1_1 = self.rib1.align(euklid.vector.Vector2D([0, 0]))
        p1_2 = self.rib1.align(euklid.vector.Vector2D([1, 0]))
        p2_1 = self.rib2.align(euklid.vector.Vector2D([0, 0]))
        p2_2 = self.rib2.align(euklid.vector.Vector2D([1, 0]))

        return 0.5 * ((p1_2 - p1_1).cross(p2_1 - p1_1).length() + (p2_2-p2_1).cross(p2_2-p1_2).length())

    @property
    def projected_area(self) -> float:
        """ return the z component of the crossproduct
            of the cell diagonals"""
        p1_1 = self.rib1.align(euklid.vector.Vector2D([0, 0]))
        p1_2 = self.rib1.align(euklid.vector.Vector2D([1, 0]))
        p2_1 = self.rib2.align(euklid.vector.Vector2D([0, 0]))
        p2_2 = self.rib2.align(euklid.vector.Vector2D([1, 0]))

        return -0.5 * (p2_1-p1_2).cross(p2_2-p1_1)[2]

    @property
    def centroid(self) -> euklid.vector.Vector3D:
        p1_1 = self.rib1.align(euklid.vector.Vector2D([0, 0]))
        p1_2 = self.rib1.align(euklid.vector.Vector2D([1, 0]))
        p2_1 = self.rib2.align(euklid.vector.Vector2D([0, 0]))
        p2_2 = self.rib2.align(euklid.vector.Vector2D([1, 0]))

        centroid = (p1_1 + p1_2 + p2_1 + p2_2) / 4
        return centroid

    @property
    def aspect_ratio(self) -> float:
        return self.span ** 2 / self.area

    def mirror(self, mirror_ribs: bool=True) -> None:
        self.rib2, self.rib1 = self.rib1, self.rib2

        if mirror_ribs:
            for rib in self.ribs:
                rib.mirror()

        for diagonal in self.diagonals:
            diagonal.mirror()

        for strap in self.straps:
            strap.mirror()
        
        cuts = list()
        for panel in self.panels:
            if panel.cut_front not in cuts:
                cuts.append(panel.cut_front)
            if panel.cut_back not in cuts:
                cuts.append(panel.cut_back)
        
        for cut in cuts:
            cut.mirror()

    def mean_airfoil(self, num_midribs: int=8) -> pyfoil.Airfoil:
        mean_rib = self.midrib(0).flatten().normalized()

        for i in range(1, num_midribs):
            y = i/(num_midribs-1)
            mean_rib += self.midrib(y).flatten().normalized()
        return mean_rib * (1. / num_midribs)

    def get_mesh_grid(self, numribs: int=0, half_cell: bool=False) -> List[List[Vertex]]:
        """
        Get Cell-grid
        :param numribs: number of miniribs to calculate
        :return: grid
        """
        numribs += 1

        grid: List[List[Vertex]] = []
        rib_indices = range(numribs + 1)
        if half_cell:
            rib_indices = rib_indices[(numribs) // 2:]
        for rib_no in rib_indices:
            y = rib_no / max(numribs, 1)
            rib = self.midrib(y).curve.nodes
            grid.append(Vertex.from_vertices_list(rib[:-1]))
        return grid

    def get_mesh(self, numribs: int=0, half_cell: bool=False) -> Mesh:
        """
        Get Cell-mesh
        :param numribs: number of miniribs to calculate
        :return: mesh
        """

        grid = self.get_mesh_grid(numribs=numribs, half_cell=half_cell)

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

    @cached_function("self")
    def get_flattened_cell(self, numribs: int=50, num_inner: Optional[int]=None) -> FlattenedCell:
        midribs = self.get_midribs(numribs)
        numpoints = len(midribs[0].curve.nodes)

        len_dct = {}
        def get_length(ik1: float, ik2: float) -> float:
            index_str = f"{ik1}:{ik2}"
            if index_str not in len_dct:
                points = []
                for i, rib in enumerate(midribs):
                    x = ik1 + i/(numribs-1) * (ik2-ik1)
                    points.append(rib[x])
                
                line = euklid.vector.PolyLine3D(points)

                len_dct[index_str] = line.get_length()

            return len_dct[index_str]

        l_0 = get_length(0, 0)

        left_bal = [euklid.vector.Vector2D([0, 0])]
        right_bal = [euklid.vector.Vector2D([l_0, 0])]

        rotate_left = euklid.vector.Rotation2D(-math.pi/2)
        rotate_right = euklid.vector.Rotation2D(math.pi/2)

        def get_point(p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D, l_0: float, l_l: float, l_r: float, left: bool=True) -> euklid.vector.Vector2D:
            lx = (l_0**2 + l_l**2 - l_r**2) / (2*l_0)
            ly_sq = l_l**2 - lx**2
            if ly_sq > 0:
                ly = math.sqrt(ly_sq)
            else:
                ly = 0
            diff = (p2 - p1).normalized()
            if left:
                diff_y = rotate_right.apply(diff)
            else:
                diff_y = rotate_left.apply(diff)

            return p1 + diff*lx + diff_y*ly


        for i in range(numpoints-1):
            p1 = left_bal[-1]
            p2 = right_bal[-1]


            d_l = (midribs[0][i] - midribs[0][i+1]).length()
            d_r = (midribs[-1][i] - midribs[-1][i+1]).length()
            l_0 = get_length(i, i)

            if False:
                pr_2 = get_point(p2, pl_2, get_length(i+1, i), d_r, get_length(i+1, i+1), left=False)
                pl_2 = get_point(p1, p2, l_0, d_l, get_length(i+1, i))
            else:
                pr_2 = get_point(p2, p1, l_0, d_r, get_length(i, i+1), left=False)
                pl_2 = get_point(p1, pr_2, get_length(i, i+1), d_l, get_length(i+1, i+1))

            left_bal.append(pl_2)
            right_bal.append(pr_2)
            #right_bal.append(get_point(p2, p1, l_0, d_r, get_length(i, i+1), left=False))

        ballooned = (
            euklid.vector.PolyLine2D(left_bal),
            euklid.vector.PolyLine2D(right_bal)
        )

        inner = []

        if num_inner is None:
            num_inner = numribs+2

        for x in openglider.utils.linspace(0, 1, num_inner):
            inner.append(ballooned[0].mix(ballooned[1], x))

        #ballooned = [left_bal, right_bal]

        return FlattenedCell(
            inner=inner,
            ballooned=ballooned
        )
    
    def calculate_3d_shaping(self, panels: Optional[List[Panel]]=None, numribs: int=10) -> None:
        if panels is None:
            panels = self.panels

        flat = self.get_flattened_cell(numribs)

        cuts_3d: Dict[int, List[float]] = {}

        def add_amount(cut: PanelCut, amount: List[float]) -> None:
            cut_key = cut.__hash__()

            for key in cuts_3d:
                if key == cut_key:
                    old = cuts_3d[key]

                    cuts_3d[key] = [(x1+x2)/2 for x1, x2 in zip(old, amount)]
                    return

            cuts_3d[cut_key] = amount

        def get_amount(cut: PanelCut) -> List[float]:
            cut_key = cut.__hash__()
            data = cuts_3d[cut_key]
            # TODO: Investigate
            return [max(0, x) for x in data]

        midribs = self.get_midribs(len(flat.inner))

        for panel in panels:
            amount_front, amount_back = panel.integrate_3d_shaping(self, self.sigma_3d_cut, flat.inner, midribs)

            add_amount(panel.cut_front, amount_front)
            add_amount(panel.cut_back, amount_back)

        cut_3d_types = [PANELCUT_TYPES.cut_3d]
        for panel in panels:
            if panel.cut_front.cut_type in cut_3d_types:
                panel.cut_front.cut_3d_amount = get_amount(panel.cut_front)
            else:
                panel.cut_front.cut_3d_amount = [0] * (numribs+2)
            
            if panel.cut_back.cut_type in cut_3d_types:
                panel.cut_back.cut_3d_amount = get_amount(panel.cut_back)
            else:
                panel.cut_back.cut_3d_amount = [0] * (numribs+2)

