from __future__ import division

import numpy as np

from openglider.airfoil import Profile2D
from openglider.glider import Glider
from openglider.glider.cell import Panel, DiagonalRib, TensionStrapSimple, Cell
from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.export_ods import export_ods_2d
from openglider.glider.parametric.import_ods import import_ods_2d
from openglider.glider.parametric.lines import LineSet2D, UpperNode2D
from openglider.glider.rib import RibHole, RigidFoil, Rib
from openglider.glider.parametric.fitglider import fit_glider_3d


class ParametricGlider(object):
    """
    A parametric (2D) Glider object used for gui input
    """
    num_arc_positions = 60
    num_shape = 30
    num_interpolate_ribs = 40
    num_cell_dist = 30
    num_depth_integral = 100

    def __init__(self, shape, arc, aoa, profiles, profile_merge_curve,
                 balloonings, ballooning_merge_curve, lineset,
                 speed, glide, zrot, elements=None):
        self.zrot = zrot or aoa
        self.shape = shape
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

    def export_ods(self, path):
        return export_ods_2d(self, path)

    @property
    def arc_positions(self):
        return self.arc.get_arc_positions(self.shape.rib_x_values)

    def get_arc_angles(self, arc_curve=None):
        """
        Get rib rotations
        :param arc_curve:
        :return: rotation angles
        """
        arc_curve = ArcCurve(self.arc)

        return arc_curve.get_rib_angles(self.shape.rib_x_values)

    @property
    def attachment_points(self):
        """coordinates of the attachment_points"""
        return [a_p.get_2d(self)
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
        first = self.profiles[i]
        if k > 0:
            second = self.profiles[i + 1]
            airfoil = first * (1 - k) + second * k
        else:
            airfoil = first.copy()
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
            cells = [[] for _ in range(self.half_cell_num)]
        else:
            cells = [cell.panels for cell in glider_3d.cells]
            for cell in cells:
                cell = []

        for cell_no, panel_lst in enumerate(cells):
            _cuts = self.elements.get("cuts", [])
            cuts = [cut for cut in _cuts if cell_no in cut["cells"]]

            # add trailing edge (2x)
            all_values = [c["left"] for c in cuts] + [c["right"] for c in cuts]
            if -1 not in all_values:
                cuts.append({"cells": [cell_no], "type": "parallel",
                             "left": -1, "right": -1})
            if 1 not in all_values:
                cuts.append({"cells": [cell_no], "type": "parallel",
                            "left": 1, "right": 1})

            cuts.sort(key=lambda cut: cut["left"])
            cuts.sort(key=lambda cut: cut["right"])

            part_no = 0
            for cut_no in range(len(cuts)-1):
                cut1 = cuts[cut_no].copy()
                cut2 = cuts[cut_no+1].copy()

                cut1.pop("cells")
                cut2.pop("cells")

                if cut1["type"] == cut2["type"] == "folded":
                    # entry
                    continue

                assert cut2["left"] >= cut1["left"]
                assert cut2["right"] >= cut1["right"]

                try:
                    material_code = self.elements["materials"][cell_no][part_no]
                except (KeyError, IndexError):
                    material_code = "unknown"

                panel = Panel(cut1, cut2,
                              name="cell{}p{}".format(cell_no, part_no),
                              material_code=material_code)
                panel_lst.append(panel)

                part_no += 1

        return cells

    def apply_diagonals(self, glider):
        for cell_no, cell in enumerate(glider.cells):
            cell.diagonals = []
            cell.straps = []
            for diagonal in self.elements.get("diagonals", []):
                if cell_no in diagonal["cells"]:
                    dct = diagonal.copy()
                    dct.pop("cells")
                    cell.diagonals.append(DiagonalRib(**dct))

            cell.diagonals.sort(key=lambda d: d.get_average_x())

            for strap in self.elements.get("straps", []):
                if cell_no in strap["cells"]:
                    dct = strap.copy()
                    dct.pop("cells")
                    dct["name"] = "cell{}strap".format(cell_no)
                    cell.straps.append(TensionStrapSimple(**dct))

            cell.straps.sort(key=lambda s: (s.left + s.right)/2)

            # Name elements

            for d_no, diagonal in enumerate(cell.diagonals):
                diagonal.name = "cell{}drib{}".format(cell_no, d_no)

            for s_no, strap in enumerate(cell.straps):
                strap.name = "cell{}strap{}".format(cell_no, s_no)

    @classmethod
    def fit_glider_3d(cls, glider, numpoints=3):
        return fit_glider_3d(cls, glider, numpoints)

    def get_glider_3d(self, glider=None, num=50):
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

        profile_x_values = self.profiles[0].x_values

        rib_holes = self.elements.get("holes", [])
        rigids = self.elements.get("rigidfoils", [])

        cell_centers = [(p1+p2)/2 for p1, p2 in zip(x_values[:-1], x_values[1:])]

        for rib_no, pos in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]
            startpoint = np.array([-front[1], arc[0], arc[1]])
            chord = abs(front[1]-back[1])
            factor = profile_merge_curve(abs(pos))
            profile = self.get_merge_profile(factor)
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
                name="rib{}".format(rib_no)
            ))
            ribs[-1].aoa_relative = aoa_int(pos)

        if self.shape.has_center_cell:
            ribs.insert(0, ribs[0].copy())
            ribs[0].arcang *= -1
            ribs[0].pos[1] *= -1
            cell_centers.insert(0, 0.)

        glider.cells = []
        for cell_no, (rib1, rib2) in enumerate(zip(ribs[:-1], ribs[1:])):
            ballooning_factor = ballooning_merge_curve(cell_centers[cell_no])
            ballooning = self.merge_ballooning(ballooning_factor)
            cell = Cell(rib1, rib2, ballooning, name="c{}".format(cell_no))

            glider.cells.append(cell)

        glider.close_rib()

        self.get_panels(glider)
        self.apply_diagonals(glider)
        #self.apply_holes(glider)

        glider.rename_parts()

        glider.lineset = self.lineset.return_lineset(glider, self.v_inf)
        glider.lineset.recalc()

        return glider

    @property
    def v_inf(self):
        angle = np.arctan(1/self.glide)
        return np.array([np.cos(angle), 0, np.sin(angle)]) * self.speed


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