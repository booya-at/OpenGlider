import numpy as np

from openglider.vector import PolyLine2D, Interpolation
from openglider.vector.spline import SymmetricBezier, Bezier
from openglider.airfoil import Profile2D
from openglider.glider.glider_2d.lines import LineSet2D, UpperNode2D
from openglider.glider.glider_2d.export_ods import export_ods_2d
from openglider.glider.glider_2d.import_ods import import_ods_2d
from openglider.glider.glider_2d.arc import ArcCurve
from openglider.glider import Glider
from openglider.glider.cell import Panel, DiagonalRib, TensionStrapSimple, Cell
from openglider.glider.rib import RibHole, RigidFoil, Rib
from openglider.glider.shape import Shape


class Glider2D(object):
    """
    A parametric (2D) Glider object used for gui input
    """
    num_arc_positions = 60
    num_shape = 30
    num_interpolate_ribs = 40
    num_cell_dist = 30
    num_depth_integral = 100

    def __init__(self, front, back, cell_dist, cell_num,
                 arc, aoa, profiles, profile_merge_curve,
                 balloonings, ballooning_merge_curve, lineset,
                 speed, glide, elements=None):
        self.front = front
        self.back = back
        self.cell_num = cell_num  # updates cell pos
        self.cell_dist = cell_dist
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
            "front": self.front,
            "back": self.back,
            "cell_dist": self.cell_dist,
            "cell_num": self.cell_num,
            "arc": self.arc,
            "aoa": self.aoa,
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
    def has_center_cell(self):
        return self.cell_num % 2

    @property
    def half_cell_num(self):
        return self.cell_num // 2 + self.has_center_cell

    @property
    def half_rib_num(self):
        return self.half_cell_num + 1

    @property
    def arc_positions(self):
        arc_curve = ArcCurve(self.arc)

        return arc_curve.get_arc_positions(self.rib_x_values)

    def get_arc_angles(self, arc_curve=None):
        """
        Get rib rotations
        :param arc_curve:
        :return: rotation angles
        """
        arc_curve = ArcCurve(self.arc)

        return arc_curve.get_rib_angles(self.rib_x_values)

    @property
    def half_shape(self):
        """
        Return shape of the glider:
        [ribs, front, back]
        """
        num = self.num_shape
        front_int = self.front.interpolation(num=num)
        back_int = self.back.interpolation(num=num)
        dist = self.rib_x_values
        front = [[x, front_int(x)] for x in dist]
        back = [[x, back_int(x)] for x in dist]

        return Shape(PolyLine2D(front), PolyLine2D(back))

    @property
    def shape(self):
        """
        Return shape of the glider:
        [ribs, front, back]
        """
        return self.half_shape.copy_complete()

    @property
    def ribs(self):
        num = self.num_interpolate_ribs
        front_int = self.front.interpolation(num=num)
        back_int = self.back.interpolation(num=num)

        dist = self.rib_x_values
        front = [[x, front_int(x)] for x in dist]
        back = [[x, back_int(x)] for x in dist]
        if self.has_center_cell:
            front.insert(0, [-front[0][0], front[0][1]])
            back.insert(0, [-back[0][0], back[0][1]])

        return list(zip(front, back))

    def get_shape_point(self, rib_no, x):
        ribs = list(self.ribs)
        rib = ribs[rib_no]
        return rib[0][0], rib[0][1] + x * (rib[1][1] - rib[0][1])

    def set_span(self, span=None):
        """
        rescale BezierCurves to given span (or front-line)
        """
        span = span or self.front.controlpoints[-1][0]

        def set_span(attribute):
            el = getattr(self, attribute)
            assert el is not None, "Not a Beziercurve: {}".format(attribute)
            factor = span/el.controlpoints[-1][0]
            el.controlpoints = [[p[0]*factor, p[1]] for p in el.controlpoints]

        for attr in ('back', 'front', 'cell_dist', 'aoa',
                     'profile_merge_curve', 'ballooning_merge_curve'):
            set_span(attr)

        arc_pos = self.arc_positions
        arc_length = arc_pos.get_length() + arc_pos[0][0]  # add center cell
        factor = span/arc_length
        self.arc.controlpoints = [[p[0]*factor, p[1]*factor]
                                  for p in self.arc.controlpoints]

    @property
    def cell_dist_controlpoints(self):
        return self.cell_dist.controlpoints[1:-1]

    @cell_dist_controlpoints.setter
    def cell_dist_controlpoints(self, arr):
        x0 = self.front.controlpoints[-1][0]
        self.cell_dist.controlpoints = [[0, 0]] + arr + [[x0, 1]]

    @property
    def cell_dist_interpolation(self):
        """
        Interpolate Cell-distribution
        """
        data = self.cell_dist.get_sequence(self.num_cell_dist)
        interpolation = Interpolation([[p[1], p[0]] for p in data])
        start = (self.has_center_cell) / self.cell_num
        num = self.cell_num // 2 + 1
        return [[interpolation(i), i] for i in np.linspace(start, 1, num)]

    @property
    def rib_x_values(self):
        return [p[0] for p in self.cell_dist_interpolation]

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
        Create Panels Objects and apply on gliders cells if provided
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

        def symmetric_fit(polyline, numpoints=numpoints):
            mirrored = PolyLine2D(polyline[1:]).mirror([0, 0], [0, 1])
            symmetric = mirrored[::-1].join(polyline[glider.has_center_cell:])
            return SymmetricBezier.fit(symmetric, numpoints=numpoints)

        front_bezier = symmetric_fit(front)
        back_bezier = symmetric_fit(back)
        arc_bezier = symmetric_fit(arc)
        aoa_bezier = symmetric_fit(aoa)

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

        # TODO: lineset, dist-curce->xvalues

        return cls(front=front_bezier,
                   back=back_bezier,
                   cell_dist=rib_distribution,
                   cell_num=cell_num,
                   arc=arc_bezier,
                   aoa=aoa_bezier,
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

        span = self.front.controlpoints[-1][0]
        self.set_span(span)

        x_values = self.rib_x_values

        front_int = self.front.interpolation(num=num)
        back_int = self.back.interpolation(num=num)
        profile_merge_curve = self.profile_merge_curve.interpolation(num=num)
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(num=num)
        aoa_int = self.aoa.interpolation(num=num)

        arc_pos = list(self.arc_positions)
        arc_angles = self.get_arc_angles()

        profile_x_values = self.profiles[0].x_values

        rib_holes = self.elements.get("holes", [])
        rigids = self.elements.get("rigidfoils", [])

        cell_centers = [(p1+p2)/2 for p1, p2 in zip(x_values[:-1], x_values[1:])]

        for rib_no, pos in enumerate(x_values):
            front = front_int(pos)
            back = back_int(pos)
            arc = arc_pos[rib_no]
            factor = profile_merge_curve(abs(pos))
            profile = self.get_merge_profile(factor)
            profile.x_values = profile_x_values

            this_rib_holes = [RibHole(ribhole["pos"], ribhole["size"]) for ribhole in rib_holes if rib_no in ribhole["ribs"]]
            this_rigid_foils = [RigidFoil(rigid["start"], rigid["end"], rigid["distance"]) for rigid in rigids if rib_no in rigid["ribs"]]

            ribs.append(Rib(
                profile_2d=profile,
                startpoint=np.array([-front, arc[0], arc[1]]),
                chord=abs(front - back),
                arcang=arc_angles[rib_no],
                glide=self.glide,
                aoa_absolute=aoa_int(pos),
                holes=this_rib_holes,
                rigidfoils=this_rigid_foils,
                name="rib{}".format(rib_no)
            ))
            ribs[-1].aoa_relative = aoa_int(pos)

        if self.has_center_cell:
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
        glider.lineset._calc_geo()
        glider.lineset._calc_sag()
        return glider


    @property
    def v_inf(self):
        angle = np.arctan(1/self.glide)
        return self.speed * np.array([np.cos(angle), 0, np.sin(angle)])

    def scale_x_y(self, value):
        self.front._data *= value
        self.back._data *= value
        self.ballooning_merge_curve._data[:, 0] *= value
        self.profile_merge_curve._data[:, 0] *= value
        self.cell_dist._data[:, 0] *= value
        self.aoa._data[:, 0] *= value

    def scale_x(self, value):
        self.front._data[:, 0] *= value
        self.back._data[:, 0] *= value
        self.ballooning_merge_curve._data[:, 0] *= value
        self.profile_merge_curve._data[:, 0] *= value
        self.cell_dist._data[:, 0] *= value
        self.aoa._data[:, 0] *= value
        self.arc._data[:, 0] *= value

    def scale_y(self, value):
        self.front._data[:, 1] *= value
        self.back._data[:, 1] *= value

    @property
    def flat_area(self):
        return self.shape.area

    def set_flat_area(self, value, fixed="aspect_ratio"):
        area = self.flat_area
        if fixed == "aspect_ratio":
            self.scale_x_y(np.sqrt(value / area))
        if fixed == "span":
            self.scale_y(value / area)

    @property
    def aspect_ratio(self):
        return self.span ** 2 / self.flat_area

    @property
    def span(self):
        return 2 * self.rib_x_values[-1]

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