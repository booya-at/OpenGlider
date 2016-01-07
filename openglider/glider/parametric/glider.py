from __future__ import division

import numpy as np

from openglider.airfoil import Profile2D
from openglider.glider import Glider
from openglider.glider.cell import Panel, DiagonalRib, TensionStrapSimple, Cell
from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.export_ods import export_ods_2d
from openglider.glider.parametric.import_ods import import_ods_2d
from openglider.glider.parametric.lines import LineSet2D, UpperNode2D
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.rib import RibHole, RigidFoil, Rib
from openglider.glider.shape import Shape
from openglider.vector import PolyLine2D, Interpolation
from openglider.vector.spline import SymmetricBezier, Bezier


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
    def v_inf(self):
        angle = np.arctan(1/self.glide)
        return np.array([-np.cos(angle), 0, np.sin(angle)]) * self.speed

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

        return arc_curve.get_rib_angles(self.rib_x_values)

    def set_span(self, span=None):
        """
        rescale BezierCurves to given span (or front-line)
        """
        span = span or self.span

        self.shape.span = span
        self.arc.rescale(self.shape.rib_x_values)

        def set_span(attribute):
            el = getattr(self, attribute)
            assert el is not None, "Not a Beziercurve: {}".format(attribute)
            factor = span/el.controlpoints[-1][0]
            el.controlpoints = [[p[0]*factor, p[1]] for p in el.controlpoints]

        for attr in ('aoa', 'profile_merge_curve', 'ballooning_merge_curve'):
            set_span(attr)



    @property
    def cell_dist_controlpoints(self):
        return self.cell_dist.controlpoints[1:-1]

    @cell_dist_controlpoints.setter
    def cell_dist_controlpoints(self, arr):
        x0 = self.front.controlpoints[-1][0]
        self.cell_dist.controlpoints = [[0, 0]] + arr + [[x0, 1]]

    @property
    def depth_integrated(self):
        """
        Return A(x)
        """
        num = self.num_depth_integral
        x_values = np.linspace(0, self.front.controlpoints[-1][0], num)
        front_int = self.front.interpolation(num=num)
        back_int = self.back.interpolation(num=num)
        integrated_depth = [0.]
        for x in x_values[1:]:
            depth = front_int(x) - back_int(x)
            integrated_depth.append(integrated_depth[-1] + 1. / depth)
        y_values = [i / integrated_depth[-1] for i in integrated_depth]
        return zip(x_values, y_values)

    def set_const_cell_dist(self):
        const_dist = list(self.depth_integrated)
        num_pts = len(self.cell_dist.controlpoints)
        self.cell_dist = self.cell_dist.fit(const_dist, numpoints=num_pts)

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
        """
        Create a parametric model from glider
        """
        shape = glider.shape_simple
        front, back = shape.front, shape.back
        arc = [rib.pos[1:] for rib in glider.ribs]
        aoa = [[front[i][0], rib.aoa_relative] for i, rib in enumerate(glider.ribs)]
        zrot = [[front[i][0], rib.zrot] for i, rib in enumerate(glider.ribs)]

        def symmetric_fit(polyline, numpoints=numpoints):
            mirrored = PolyLine2D(polyline[1:]).mirror([0, 0], [0, 1])
            symmetric = mirrored[::-1].join(polyline[glider.has_center_cell:])
            return SymmetricBezier.fit(symmetric, numpoints=numpoints)

        front_bezier = symmetric_fit(front)
        back_bezier = symmetric_fit(back)
        arc_bezier = symmetric_fit(arc)
        aoa_bezier = symmetric_fit(aoa)
        zrot_bezier = symmetric_fit(zrot)

        cell_num = len(glider.cells) * 2 - glider.has_center_cell

        front[0][0] = 0  # for midribs
        start = (2 - glider.has_center_cell) / cell_num
        const_arr = [0.] + np.linspace(start, 1, len(front) - 1).tolist()

        rib_pos = [p[0] for p in front]
        cell_centers = [(p1+p2)/2 for p1, p2 in zip(rib_pos[:-1], rib_pos[1:])]

        rib_pos_int = Interpolation(zip([0] + rib_pos[1:], const_arr))
        rib_distribution = [[i, rib_pos_int(i)] for i in np.linspace(0, rib_pos[-1], 30)]
        rib_distribution = Bezier.fit(rib_distribution, numpoints=numpoints+3)

        profiles = [rib.profile_2d for rib in glider.ribs]
        profile_dist = Bezier.fit([[i, i] for i, rib in enumerate(front)],
                                       numpoints=numpoints)

        balloonings = [cell.ballooning for cell in glider.cells]
        ballooning_dist = Bezier.fit([[i, i] for i, rib in enumerate(front[1:])],
                                       numpoints=numpoints)

        zrot = Bezier([[0, 0], [front.last()[0], 0]])

        # TODO: lineset, dist-curce->xvalues

        parametric_shape = ParametricShape(front, back, rib_distribution, cell_num)
        parametric_arc = ArcCurve(arc_bezier)

        return cls(shape=parametric_shape,
                   arc=parametric_arc,
                   aoa=aoa_bezier,
                   zrot=zrot,
                   profiles=profiles,
                   profile_merge_curve=profile_dist,
                   balloonings=balloonings,
                   ballooning_merge_curve=ballooning_dist,
                   glide=glider.glide,
                   speed=10,
                   lineset=LineSet2D([]))

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
        return self.speed * np.array([np.cos(angle), 0, np.sin(angle)])

    def scale(self, x=1, y=1):
        self.front.controlpoints = [p*[x, y] for p in self.front.controlpoints]
        self.back.controlpoints = [p*[x, y] for p in self.back.controlpoints]

        if x != 1:
            #self.cell_dist.controlpoints = [p*[x,1] for p in self.cell_dist.controlpoints]
            self.rescale_curves()

    def rescale_curves(self):
        #span = self.span
        span = self.shape.span

        def rescale(curve):
            span_orig = curve.controlpoints[-1][0]
            factor = span/span_orig
            curve.controlpoints = [[p[0]*factor, p[1]] for p in curve.controlpoints]

        rescale(self.ballooning_merge_curve)
        rescale(self.profile_merge_curve)
        rescale(self.aoa)

    @property
    def flat_area(self):
        return self.shape.area

    def set_flat_area(self, value, fixed="aspect_ratio"):
        self.shape.set_area(value, fixed=fixed)

    @property
    def aspect_ratio(self):
        return self.span ** 2 / self.flat_area

    @property
    def span(self):
        return 2 * self.shape.span

    def set_aspect_ratio(self, value, fixed="span"):
        ar0 = self.aspect_ratio
        if fixed == "span":
            self.scale_y(ar0 / value)
        elif fixed == "area":
            self.scale_y(np.sqrt(ar0 / value))
            self.scale_x(np.sqrt(value / ar0))

    def set_span_1(self, value, fixed="area"):     # integrate in set span
        sp0 = self.span / 2
        if fixed == "area":
            self.scale_x(value / sp0)
            self.scale_y(sp0 / value)
        if fixed == "aspect_ratio":
            self.scale_x_y(value / sp0)