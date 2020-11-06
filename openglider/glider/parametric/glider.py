from __future__ import division

import math
import numpy as np
import copy

from openglider.glider.parametric.shape import ParametricShape
from openglider.airfoil import Profile2D
from openglider.glider.glider import Glider
from openglider.glider.cell import Panel, DiagonalRib, TensionStrap, TensionLine, Cell
from openglider.glider.cell.elements import PanelRigidFoil
from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.export_ods import export_ods_2d
from openglider.glider.parametric.import_ods import import_ods_2d
from openglider.glider.parametric.lines import LineSet2D, UpperNode2D
from openglider.glider.rib import RibHole, RigidFoil, Rib, MiniRib
from openglider.glider.parametric.fitglider import fit_glider_3d
from openglider.utils.distribution import Distribution
from openglider.utils.table import Table
from openglider.utils import ZipCmp


class ParametricGlider(object):
    """
    A parametric (2D) Glider object used for gui input
    """
    num_arc_positions = 60
    num_shape = 30
    num_interpolate_ribs = 40
    num_cell_dist = 30
    num_depth_integral = 100
    num_interpolate = 30
    num_profile = None

    def __init__(self, shape, arc, aoa, profiles, profile_merge_curve,
                 balloonings, ballooning_merge_curve, lineset,
                 speed, glide, zrot, elements=None):
        self.zrot = zrot or aoa
        self.shape: ParametricShape = shape
        self.arc = arc
        self.aoa = aoa
        self.profiles = profiles or []
        self.profile_merge_curve = profile_merge_curve
        self.balloonings = balloonings or []
        self.ballooning_merge_curve = ballooning_merge_curve
        self.lineset = lineset or LineSet2D([])
        self.speed = speed
        self.glide = glide
        self.elements = elements or {}

    def __json__(self):
        return {
            "shape": self.shape,
            "arc": self.arc,
            "aoa": self.aoa,
            "zrot": self.zrot,
            "profiles": self.profiles,
            "profile_merge_curve": self.profile_merge_curve,
            "balloonings": self.balloonings,
            "ballooning_merge_curve": self.ballooning_merge_curve,
            "lineset": self.lineset,
            "speed": self.speed,
            "glide": self.glide,
            "elements": self.elements
        }

    @classmethod
    def import_ods(cls, path):
        return import_ods_2d(cls, path)

    export_ods = export_ods_2d

    def copy(self):
        return copy.deepcopy(self)

    def get_geomentry_table(self):
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

        last_angle = 0
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


    @property
    def arc_positions(self):
        return self.arc.get_arc_positions(self.shape.rib_x_values)

    def get_arc_angles(self, arc_curve=None):
        """
        Get rib rotations
        :param arc_curve:
        :return: rotation angles
        """
        #arc_curve = ArcCurve(self.arc)
        arc_curve = self.arc

        return arc_curve.get_rib_angles(self.shape.rib_x_values)

    @property
    def attachment_points(self):
        """coordinates of the attachment_points"""
        return [a_p.get_2D(self.shape)
                for a_p in self.lineset.nodes
                if isinstance(a_p, UpperNode2D)]

    def merge_ballooning(self, factor):
        factor = max(0, min(len(self.balloonings)-1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.balloonings[i]
        if k > 0:
            second = self.balloonings[i + 1]
            return first * (1 - k) + second * k
        else:
            return first.copy()

    def get_merge_profile(self, factor):
        factor = max(0, min(len(self.profiles)-1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.profiles[i].copy()
        if k > 0:
            second = self.profiles[i + 1]
            airfoil = first * (1 - k) + second * k
        else:
            airfoil = first
        return Profile2D(airfoil.data)

    def get_panels(self, glider_3d=None):
        """
        Create Panels Objects and apply on gliders cells if provided, otherwise create a list of panels
        :param glider_3d: (optional)
        :return: list of "cells"
        """
        def is_greater(cut_1, cut_2):
            if cut_1["left"] >= cut_2["left"] and cut_1["right"] >= cut_2["left"]:
                return True
            return False

        if glider_3d is None:
            cells = [[] for _ in range(self.shape.half_cell_num)]
        else:
            cells = [cell.panels for cell in glider_3d.cells]
            for cell in cells:
                cell = []

        for cell_no, panel_lst in enumerate(cells):
            _cuts = self.elements.get("cuts", [])
            cuts = [cut.copy() for cut in _cuts if cell_no in cut["cells"]]
            for cut in cuts:
                cut.pop("cells")

            # add trailing edge (2x)
            all_values = [c["left"] for c in cuts] + [c["right"] for c in cuts]
            #print(all_values, 1 in all_values)
            if -1 not in all_values:
                cuts.append({"type": "parallel",
                             "left": -1, "right": -1})
            if 1 not in all_values:
                cuts.append({"type": "parallel",
                            "left": 1, "right": 1})

            cuts.sort(key=lambda cut: cut["left"])

            for cut1, cut2 in ZipCmp(cuts):
                part_no = len(panel_lst)
                #print(cut1["left"], cut2["left"], cut2["right"], i, len(cuts))
                if cut1["right"] > cut2["right"]:
                    error_str = "Invalid cut: C{} {:.02f}/{:.02f}/{} + {:.02f}/{:.02f}/{}".format(
                        cell_no+1,
                        cut1["left"], cut1["right"], cut1["type"],
                        cut2["left"], cut2["right"], cut2["type"],
                    )
                    raise ValueError(error_str)

                if (cut1["type"] == cut2["type"] == "folded" or
                    cut1["type"] == cut2["type"] == "singleskin"):
                    # entry
                    continue

                try:
                    material_code = self.elements["materials"][cell_no][part_no]
                except (KeyError, IndexError):
                    material_code = "unknown"

                panel = Panel(cut1, cut2,
                              name="c{}p{}".format(cell_no+1, part_no+1),
                              material_code=material_code)
                panel_lst.append(panel)


        return cells

    def _get_cell_straps(self, name, _cls):
        elements = []
        for cell_no in range(self.shape.half_cell_num):
            cell_elements = []
            for strap in self.elements.get(name, []):
                if cell_no in strap["cells"]:
                    dct = strap.copy()
                    dct.pop("cells")
                    cell_elements.append(_cls(**dct))

            cell_elements.sort(key=lambda strap: strap.get_average_x())

            for strap_no, strap in enumerate(cell_elements):
                strap.name = "c{}{}{}".format(cell_no+1, name[0], strap_no)
            
            elements.append(cell_elements)
        
        return elements

    def get_cell_diagonals(self):
        return self._get_cell_straps("diagonals", DiagonalRib)
    
    def get_cell_straps(self):
        return self._get_cell_straps("straps", TensionStrap)
    
    def get_cell_tension_lines(self):
        return self._get_cell_straps("tension_lines", TensionLine)

    def apply_diagonals(self, glider):
        cell_straps = self.get_cell_straps()
        cell_diagonals = self.get_cell_diagonals()
        cell_tensionlines = self.get_cell_tension_lines()

        for cell_no, cell in enumerate(glider.cells):
            cell.diagonals = cell_diagonals[cell_no]
            cell.straps = cell_straps[cell_no]
            cell.straps += cell_tensionlines[cell_no]

    @classmethod
    def fit_glider_3d(cls, glider, numpoints=3):
        return fit_glider_3d(cls, glider, numpoints)

    def get_front_line(self):
        """
        Get Nose Positions for cells
        :return:
        """

    def get_aoa(self, interpolation_num=None):
        aoa_interpolation = self.aoa.interpolation(num=interpolation_num or self.num_interpolate)

        return [aoa_interpolation(x) for x in self.shape.rib_x_values]

    def apply_aoa(self, glider, interpolation_num=50):
        aoa_interpolation = self.aoa.interpolation(num=interpolation_num)
        aoa_values = [aoa_interpolation(x) for x in self.shape.rib_x_values]

        if self.shape.has_center_cell:
            aoa_values.insert(0, aoa_values[0])

        for rib, aoa in zip(glider.ribs, aoa_values):
            rib.aoa_relative = aoa

    def get_profile_merge(self):
        profile_merge_curve = self.profile_merge_curve.interpolation(num=self.num_interpolate)
        return [profile_merge_curve(abs(x)) for x in self.shape.rib_x_values]

    def get_ballooning_merge(self):
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(num=self.num_interpolate)
        return [ballooning_merge_curve(abs(x) for x in self.shape.cell_x_values)]

    def apply_shape_and_arc(self, glider):
        x_values = self.shape.rib_x_values
        shape_ribs = self.shape.ribs
        arc_pos = list(self.arc.get_arc_positions(x_values))
        offset_x = shape_ribs[0][0][1]

        line = []
        chords = []

        for rib_no, x in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]
            startpoint = np.array([-front[1] + offset_x, arc[0], arc[1]])

            line.append(startpoint)
            chords.append(abs(front[1]-back[1]))

        if self.shape.has_center_cell:
            line.insert(0, line[0] * [1, -1, 1])
            chords.insert(0, chords[0])

        for rib_no, p in enumerate(line):
            glider.ribs[rib_no].pos = p
            glider.ribs[rib_no].chord = chords[rib_no]

    def get_glider_3d(self, glider=None, num=50, num_profile=None):
        """returns a new glider from parametric values"""
        glider = glider or Glider()
        ribs = []

        self.rescale_curves()

        x_values = self.shape.rib_x_values
        shape_ribs = self.shape.ribs

        profile_merge_curve = self.profile_merge_curve.interpolation(num=num)
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(num=num)
        aoa_int = self.aoa.interpolation(num=num)
        zrot_int = self.zrot.interpolation(num=num)

        arc_pos = list(self.arc.get_arc_positions(x_values))
        rib_angles = self.arc.get_rib_angles(x_values)

        if self.num_profile is not None:
            num_profile = self.num_profile

        if num_profile is not None:
            profile_x_values = Distribution.from_cos_distribution(num_profile)
        else:
            profile_x_values = self.profiles[0].x_values

        rib_holes = self.elements.get("holes", [])
        rigids = self.elements.get("rigidfoils", [])

        cell_centers = [(p1+p2)/2 for p1, p2 in zip(x_values[:-1], x_values[1:])]
        offset_x = shape_ribs[0][0][1]

        rib_material = None
        if "rib_material" in self.elements:
            rib_material = self.elements["rib_material"]

        for rib_no, pos in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]
            startpoint = np.array([-front[1] + offset_x, arc[0], arc[1]])

            chord = abs(front[1]-back[1])
            factor = profile_merge_curve(abs(pos))
            profile = self.get_merge_profile(factor)
            profile.name = "Profile{}".format(rib_no)
            profile.x_values = profile_x_values

            this_rib_holes = [RibHole(ribhole["pos"], ribhole["size"]) for ribhole in rib_holes if rib_no in ribhole["ribs"]]
            this_rigid_foils = [RigidFoil(rigid["start"], rigid["end"], rigid["distance"]) for rigid in rigids if rib_no in rigid["ribs"]]

            ribs.append(Rib(
                profile_2d=profile,
                startpoint=startpoint,
                chord=chord,
                arcang=rib_angles[rib_no],
                glide=self.glide,
                aoa_absolute=aoa_int(pos),
                zrot=zrot_int(pos),
                holes=this_rib_holes,
                rigidfoils=this_rigid_foils,
                name="rib{}".format(rib_no),
                material_code=rib_material
            ))
            ribs[-1].aoa_relative = aoa_int(pos)

        if self.shape.has_center_cell:
            new_rib = ribs[0].copy()
            new_rib.name = "rib0"
            new_rib.mirror()
            new_rib.mirrored_rib = ribs[0]
            ribs.insert(0, new_rib)
            cell_centers.insert(0, 0.)

        glider.cells = []
        for cell_no, (rib1, rib2) in enumerate(zip(ribs[:-1], ribs[1:])):
            ballooning_factor = ballooning_merge_curve(cell_centers[cell_no])
            ballooning = self.merge_ballooning(ballooning_factor)
            cell = Cell(rib1, rib2, ballooning, name="c{}".format(cell_no+1))

            glider.cells.append(cell)

        glider.close_rib()

        # CELL-ELEMENTS
        self.get_panels(glider)
        self.apply_diagonals(glider)

        for minirib in self.elements.get("miniribs", []):
            data = minirib.copy()
            cells = data.pop("cells")
            for cell_no in cells:
                glider.cells[cell_no].miniribs.append(MiniRib(**data))

        for rigidfoil in self.elements.get("cell_rigidfoils"):
            for cell_no in rigidfoil.pop("cells"):
                glider.cells[cell_no].rigidfoils.append(PanelRigidFoil(**rigidfoil))

        # RIB-ELEMENTS
        #self.apply_holes(glider)

        glider.rename_parts()

        glider.lineset = self.lineset.return_lineset(glider, self.v_inf)
        glider.lineset.glider = glider
        glider.lineset.calculate_sag = False
        for _ in range(3):
            glider.lineset.recalc()
        glider.lineset.calculate_sag = True
        glider.lineset.recalc()

        return glider

    def apply_ballooning(self, glider3d):
        for ballooning in self.balloonings:
            ballooning.apply_splines()
        cell_centers = self.shape.cell_x_values
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(num=self.num_interpolate)
        for cell_no, cell in enumerate(glider3d.cells):
            ballooning_factor = ballooning_merge_curve(cell_centers[cell_no])
            ballooning = self.merge_ballooning(ballooning_factor)
            cell.ballooning = ballooning

        return glider3d

    @property
    def v_inf(self):
        angle = np.arctan(1/self.glide)
        return np.array([np.cos(angle), 0, np.sin(angle)]) * self.speed

    def set_area(self, area):
        factor = math.sqrt(area/self.shape.area)
        self.shape.scale(factor)
        self.lineset.scale(factor, scale_lower_floor=False)
        self.rescale_curves()

    def set_aspect_ratio(self, aspect_ratio, remain_area=True):
        ar0 = self.shape.aspect_ratio
        area0 = self.shape.area


        self.shape.scale(y=ar0 / aspect_ratio)

        for p in self.lineset.get_lower_attachment_points():
            p.pos_2D[1] *= ar0 / aspect_ratio

        if remain_area:
            self.set_area(area0)

        return self.shape.aspect_ratio



##############################################################
# is this used?
    def scale(self, x=1, y=1):
        self.shape.scale(x, y)
        if x != 1:
            self.rescale_curves()
##############################################################

    def rescale_curves(self):
        span = self.shape.span

        def rescale(curve):
            span_orig = curve.controlpoints[-1][0]
            factor = span/span_orig
            curve._data[:, 0] *= factor

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

    def export_lines2D_as_svg(self, file_name=None):
        # sollte im lineset2D sein, aber des lineset hat keine moeglichkeit auf diese Klasse
        # zuzugreifen...
        border = 0.1
        bbox = self.get_line_bbox()
        width = bbox[1][0] - bbox[0][0]
        height = bbox[1][1] - bbox[0][1]

        import svgwrite
        import svgwrite.container
        drawing = svgwrite.Drawing(size=[800, 800*height/width])

        drawing.viewbox(bbox[0][0]-border*width, -bbox[1][1]-border*height, width*(1+2*border), height*(1+2*border))
        lines = svgwrite.container.Group()
        lines.scale(1, -1)
        for line in self.lineset.lines:
            p1 = line.lower_node.get_2D(self.shape)
            p2 = line.upper_node.get_2D(self.shape)
            drawing_line = drawing.polyline([p1, p2], style="stroke:black; vector-effect: fill: none; stroke-width:0.01px")
            lines.add(drawing_line)
        drawing.add(lines)

        ribs = svgwrite.container.Group()

        ribs.scale(1, -1)
        p1_old, p2_old = None, None
        for rib in self.shape.ribs:
            p1 = rib[0]
            p2 = rib[1]
            ribs.add(drawing.polyline([p1, p2], style="stroke:black; vector-effect: fill: none; stroke-width:0.01px"))
            if p1_old and p2_old:
                ribs.add(drawing.polyline([p1_old, p1], style="stroke:black; vector-effect: fill: none; stroke-width:0.01px"))
                ribs.add(drawing.polyline([p2_old, p2], style="stroke:black; vector-effect: fill: none; stroke-width:0.01px"))
            p1_old, p2_old = p1, p2

        drawing.add(ribs)
        if file_name:
            drawing.saveas(file_name)
        return drawing.tostring()