import copy
import logging
import math
from typing import List, Tuple, Optional

import euklid
import openglider.materials
import pyfoil
from openglider.airfoil import Profile2D
from openglider.glider.ballooning.base import BallooningBase
from openglider.glider.ballooning.new import BallooningBezierNeu
from openglider.glider.cell import Cell, DiagonalRib, Panel, PanelCut, TensionLine, TensionStrap
from openglider.glider.cell.rigidfoil import PanelRigidFoil
from openglider.glider.glider import Glider
from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.export_ods import export_ods_2d
from openglider.glider.parametric.fitglider import fit_glider_3d
from openglider.glider.parametric.import_ods import import_ods_2d
from openglider.glider.parametric.lines import LineSet2D, UpperNode2D
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.table import GliderTables
from openglider.glider.parametric.table.curve import CurveTable
from openglider.glider.rib import MiniRib, Rib, SingleSkinRib
from openglider.utils import ZipCmp, linspace
from openglider.utils.dataclass import BaseModel, dataclass, field
from openglider.utils.distribution import Distribution
from openglider.utils.table import Table
from openglider.utils.types import CurveType, SymmetricCurveType

logger = logging.getLogger(__name__)


@dataclass
class ParametricGlider:
    """
    A parametric (2D) Glider object used for gui input
    """
    shape: ParametricShape
    arc: ArcCurve
    aoa: SymmetricCurveType
    profiles: List[pyfoil.Airfoil]
    profile_merge_curve: CurveType
    balloonings: List[BallooningBase]
    ballooning_merge_curve: CurveType
    lineset: LineSet2D
    speed: float
    glide: float
    tables: GliderTables = field(default_factory=lambda: GliderTables())
    zrot: SymmetricCurveType = field(default_factory=lambda: euklid.spline.SymmetricBSplineCurve([[0,0],[1,0]]))

    num_interpolate: int=30
    num_profile: Optional[int]=None

    def test(self) -> int:
        return len(self.ballooning_merge_curve.controlpoints.nodes)

    @classmethod
    def import_ods(cls, path):
        return import_ods_2d(cls, path)

    export_ods = export_ods_2d

    def copy(self):
        return copy.deepcopy(self)

    def get_geomentry_table(self) -> Table:
        table = Table()
        table.insert_row(["", "Ribs", "Chord", "X", "Y", "%", "Arc", "Arc_diff", "AOA", "Z-rotation", "Y-rotation", "profile-merge", "ballooning-merge"])
        shape = self.shape.get_half_shape()
        for rib_no in range(self.shape.half_rib_num):
            table[1+rib_no, 1] = rib_no+1

        for rib_no, chord in enumerate(shape.chords):
            table[1+rib_no, 2] = chord

        for rib_no, p in enumerate(self.shape.baseline):
            table[1+rib_no, 3] = p[0]
            table[1+rib_no, 4] = p[1]
            table[1+rib_no, 5] = self.shape.baseline_pos

        last_angle = 0.
        for cell_no, angle in enumerate(self.get_arc_angles()):
            angle = angle * 180 / math.pi
            table[1+cell_no, 6] = angle
            table[1+cell_no, 7] = angle - last_angle
            last_angle = angle

        for rib_no, aoa in enumerate(self.get_aoa()):
            table[1+rib_no, 8] = aoa * 180 / math.pi
            table[1+rib_no, 9] = 0
            table[1+rib_no, 10] = 0

        return table

    def get_arc_angles(self) -> List[float]:
        """
        Get rib rotations
        """
        return self.arc.get_rib_angles(self.shape.rib_x_values)

    @property
    def attachment_points(self) -> List[UpperNode2D]:
        """coordinates of the attachment_points"""
        return [a_p.get_2D(self.shape)
                for a_p in self.lineset.nodes
                if isinstance(a_p, UpperNode2D)]

    def merge_ballooning(self, factor, multiplier) -> BallooningBase:
        factor = max(0, min(len(self.balloonings)-1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.balloonings[i]
        if k > 0:
            second = self.balloonings[i + 1]
            result = first * (1 - k) + second * k
        else:
            result = first
        
        return result * multiplier

    def get_merge_profile(self, factor) -> pyfoil.Airfoil:
        factor = max(0, min(len(self.profiles)-1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.profiles[i]

        if k > 0:
            second = self.profiles[i + 1]
            airfoil = first * (1 - k) + second * k
        else:
            airfoil = first.copy()
        return airfoil

    def get_curves(self):
        return self.tables.curves.get_curves(self.shape.get_half_shape())

    def get_panels(self, glider_3d=None) -> List[List[Panel]]:
        """
        Create Panels Objects and apply on gliders cells if provided, otherwise create a list of panels
        :param glider_3d: (optional)
        :return: list of "cells"
        """
        curves = self.get_curves()
        def is_greater(cut_1, cut_2):
            if cut_1["left"] >= cut_2["left"] and cut_1["right"] >= cut_2["left"]:
                return True
            return False

        cells: List[List[Panel]]

        if glider_3d is None:
            cells = [[] for _ in range(self.shape.half_cell_num)]
        else:
            cells = [cell.panels for cell in glider_3d.cells]

        for cell_no, panel_lst in enumerate(cells):
            panel_lst.clear()

            cuts: List[PanelCut] = self.tables.cuts.get(cell_no, curves=curves)

            all_values = [c.x_left for c in cuts] + [c.x_right for c in cuts]

            if -1 not in all_values:
                cuts.append(PanelCut(-1, -1, PanelCut.CUT_TYPES.parallel))
            
            if 1 not in all_values:
                cuts.append(PanelCut(1, 1, PanelCut.CUT_TYPES.parallel))

            cuts.sort(key=lambda cut: cut.get_average_x())

            i = 0
            materials = self.tables.material_cells.get(cell_no)

            for cut1, cut2 in ZipCmp(cuts):
                
                if cut1.x_right > cut2.x_right or cut1.x_left > cut2.x_left:
                    error_str = "Invalid cut: C{} {:.02f}/{:.02f}/{} + {:.02f}/{:.02f}/{}".format(
                        cell_no+1,
                        cut1.x_left, cut1.x_right, cut1.cut_type,
                        cut2.x_left, cut2.x_right, cut2.cut_type
                    )
                    raise ValueError(error_str)

                if cut1.cut_type == cut2.cut_type:
                    if cut1.cut_type in (PanelCut.CUT_TYPES.folded, PanelCut.CUT_TYPES.singleskin):
                        continue

                try:
                    material = materials[i]
                except (KeyError, IndexError):
                    #logger.warning(f"No material for panel {cell_no}/{i+1}")
                    material = openglider.materials.Material(name="unknown")
                
                i += 1

                if material is not None:
                    panel = Panel(cut1, cut2,
                                name="c{}p{}".format(cell_no+1, len(panel_lst)+1),
                                material=material)
                    panel_lst.append(panel)


        return cells

    def apply_diagonals(self, glider: Glider) -> None:
        curves = self.get_curves()

        for cell_no, cell in enumerate(glider.cells):
            cell.diagonals = self.tables.diagonals.get(row_no=cell_no, curves=curves)

            cell.diagonals.sort(key=lambda strap: strap.get_average_x())

            for strap_no, strap in enumerate(cell.diagonals):
                strap.name = "c{}{}{}".format(cell_no+1, "d", strap_no)

            cell.straps = self.tables.straps.get(row_no=cell_no, curves=curves)
            cell.straps.sort(key=lambda strap: strap.get_average_x())

            for strap_no, strap in enumerate(cell.diagonals):
                strap.name = "c{}{}{}".format(cell_no+1, "s", strap_no)

    @classmethod
    def fit_glider_3d(cls, glider: Glider, numpoints=3) -> "ParametricGlider":
        return fit_glider_3d(cls, glider, numpoints)

    def get_aoa(self, interpolation_num=None) -> List[float]:
        aoa_interpolation = euklid.vector.Interpolation(self.aoa.get_sequence(interpolation_num or self.num_interpolate).nodes)

        return [aoa_interpolation.get_value(abs(x)) for x in self.shape.rib_x_values]

    def apply_aoa(self, glider: Glider) -> None:
        aoa_values = self.get_aoa()

        if self.shape.has_center_cell:
            aoa_values.insert(0, aoa_values[0])

        for rib, aoa in zip(glider.ribs, aoa_values):
            rib.aoa_relative = aoa

    def get_profile_merge(self) -> List[float]:
        profile_merge_curve = euklid.vector.Interpolation(self.profile_merge_curve.get_sequence(self.num_interpolate).nodes)
        return [profile_merge_curve.get_value(abs(x)) for x in self.shape.rib_x_values]

    def get_ballooning_merge(self) -> List[Tuple[float, float]]:
        ballooning_merge_curve = euklid.vector.Interpolation(self.ballooning_merge_curve.get_sequence(self.num_interpolate).nodes)
        factors = [ballooning_merge_curve.get_value(abs(x)) for x in self.shape.cell_x_values]

        table = self.tables.ballooning_factors

        if table is not None:
            all_factors = table.get_merge_factors(factors)
        else:
            all_factors = [(factor, 1) for factor in factors]

        return [(max(0, x), y) for x,y in all_factors]

    def apply_shape_and_arc(self, glider: Glider) -> None:
        x_values = [abs(x) for x in self.shape.rib_x_values]
        shape_ribs = self.shape.ribs

        arc_pos = list(self.arc.get_arc_positions(x_values))
        rib_angles = self.arc.get_rib_angles(x_values)

        offset_x = shape_ribs[0][0][1]

        for rib_no, x in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]
            startpoint = euklid.vector.Vector3D([-front[1] + offset_x, arc[0], arc[1]])
            rib = glider.ribs[rib_no]

            rib.pos = startpoint
            rib.chord = abs(front[1]-back[1])
            rib.arc_angle = rib_angles[rib_no]

    def get_glider_3d(self, glider: Glider=None, num=50, num_profile=None) -> Glider:
        """returns a new glider from parametric values"""
        glider = glider or Glider()
        ribs = []

        logger.info("apply curves")
        self.rescale_curves()
        curves = self.get_curves()

        x_values = self.shape.rib_x_values
        shape_ribs = self.shape.ribs

        aoa_int = euklid.vector.Interpolation(self.aoa.get_sequence(num).nodes)
        zrot_int = euklid.vector.Interpolation(self.zrot.get_sequence(num).nodes)

        arc_pos = self.arc.get_arc_positions(x_values).tolist()
        rib_angles = self.arc.get_rib_angles(x_values)

        if self.num_profile is not None:
            num_profile = self.num_profile

        if num_profile is not None:
            airfoil_distribution = Distribution.from_cos_distribution(num_profile)
        else:
            airfoil_distribution = self.profiles[0].x_values


        logger.info("apply elements")
        offset_x = shape_ribs[0][0][1]


        logger.info("create ribs")
        profile_merge_values = self.get_profile_merge()

        if self.shape.has_center_cell:
            rib_angles.insert(0, -rib_angles[0])

        for rib_no, x_value in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]

            startpoint = euklid.vector.Vector3D([-front[1] + offset_x, arc[0], arc[1]])

            try:
                material = self.tables.material_ribs.get(rib_no)[0]
            except (KeyError, IndexError):
                logger.warning(f"no material set for rib: {rib_no+1}")
                material = openglider.materials.Material(name="unknown")

            chord = abs(front[1]-back[1])
            factor = profile_merge_values[rib_no]

            merge_factor, scale_factor = self.tables.profiles.get_factors(rib_no)

            if merge_factor is not None:
                factor = merge_factor

            profile = self.get_merge_profile(factor).set_x_values(airfoil_distribution)


            if scale_factor is not None:
                profile = profile.set_thickness(profile.thickness * scale_factor)

            profile.name = "Profile{}".format(rib_no)

            if flap := self.tables.profiles.get_flap(rib_no):
                logger.warning(f"add flap: {flap}")
                profile = profile.add_flap(*flap)

            sharknose = self.tables.profiles.get_sharknose(rib_no)

            this_rib_holes = self.tables.holes.get(rib_no, curves=curves)
            this_rigid_foils = self.tables.rigidfoils_rib.get(rib_no)

            logger.warning(f"holes for rib:  {rib_no} {this_rib_holes}")
            rib = Rib(
                profile_2d=profile,
                startpoint=startpoint,
                chord=chord,
                arcang=rib_angles[rib_no],
                xrot=self.tables.rib_modifiers.get_xrot(rib_no),
                glide=self.glide,
                aoa_absolute=aoa_int.get_value(abs(x_value)),
                zrot=zrot_int.get_value(abs(x_value)),
                holes=this_rib_holes,
                rigidfoils=this_rigid_foils,
                name="rib{}".format(rib_no),
                material=material,
                sharknose=sharknose
            )
            rib.aoa_relative = aoa_int.get_value(abs(x_value))

            singleskin_data = self.tables.rib_modifiers.get(rib_no)
            if singleskin_data:
                rib = SingleSkinRib.from_rib(rib, singleskin_data[0])

            ribs.append(rib)

        logger.info("create cells")

        ballooning_factors = self.get_ballooning_merge()
        glider.cells = []
        for cell_no, (rib1, rib2) in enumerate(zip(ribs[:-1], ribs[1:])):

            ballooning_factor = ballooning_factors[cell_no]
            ballooning = self.merge_ballooning(*ballooning_factor)
            
            cell = Cell(rib1, rib2, ballooning, name="c{}".format(cell_no+1))

            cell.rigidfoils = self.tables.rigidfoils_cell.get(cell_no)

            glider.cells.append(cell)


        logger.info("create cell elements")
        # CELL-ELEMENTS
        self.get_panels(glider)
        self.apply_diagonals(glider)

        for cell_no, cell in enumerate(glider.cells):
            cell.miniribs = self.tables.miniribs.get(row_no=cell_no)

        # RIB-ELEMENTS
        #self.apply_holes(glider)
                # add stabi rib
        if self.shape.stabi_cell:
            cell = glider.cells[-1]
            ballooning = BallooningBezierNeu([[-1,0.015],[-0.7, 0.04], [-0.2, 0.04], [0, 0.02], [0.2, 0.04], [0.7, 0.04], [1,0.015]])
            cell.ballooning = ballooning

            glider.ribs[-2].profile_2d *= 0.7
        
        glider.close_rib()
        glider.rename_parts()


        logger.info("create lineset")

        glider.lineset = self.lineset.return_lineset(glider, self.v_inf)
        #glider.lineset.iterate_target_length()
        glider.lineset.recalc(glider=glider)
        glider.lineset.rename_lines()

        return glider

    def apply_ballooning(self, glider3d: Glider) -> Glider:
        for ballooning in self.balloonings:
            ballooning.apply_splines()

        ballooning_factors = self.get_ballooning_merge()

        for cell_no, cell in enumerate(glider3d.cells):
            ballooning_factor = ballooning_factors[cell_no]
            cell.ballooning = self.merge_ballooning(*ballooning_factor)

        return glider3d

    @property
    def v_inf(self) -> euklid.vector.Vector3D:
        angle = math.atan(1/self.glide)

        return euklid.vector.Vector3D([math.cos(angle), 0, math.sin(angle)]) * self.speed

    def set_area(self, area) -> None:
        factor = math.sqrt(area/self.shape.area)
        self.shape.scale(factor)
        self.lineset.scale(factor, scale_lower_floor=False)
        self.rescale_curves()

    def set_aspect_ratio(self, aspect_ratio, remain_area=True) -> float:
        ar0 = self.shape.aspect_ratio
        area0 = self.shape.area


        self.shape.scale(y=ar0 / aspect_ratio)

        for p in self.lineset.get_lower_attachment_points():
            p.pos_2D[1] *= ar0 / aspect_ratio

        if remain_area:
            self.set_area(area0)

        return self.shape.aspect_ratio

    def rescale_curves(self) -> None:
        span = self.shape.span

        def rescale(curve):
            span_orig = curve.controlpoints.nodes[-1][0]
            factor = span/span_orig
            curve.controlpoints = curve.controlpoints.scale([factor, 1])

        rescale(self.ballooning_merge_curve)
        rescale(self.profile_merge_curve)
        rescale(self.aoa)
        rescale(self.zrot)
        self.arc.rescale(self.shape.rib_x_values)

    def get_line_bbox(self):
        points = []
        for point in self.lineset.nodes:
            points.append(point.get_2D(self.shape))

        return [
            [min([p[0] for p in points]), min([p[1] for p in points])],
            [max([p[0] for p in points]), max([p[1] for p in points])],
        ]
