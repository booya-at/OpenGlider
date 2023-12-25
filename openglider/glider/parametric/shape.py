from __future__ import division
import math
import numpy as np

from openglider.glider.shape import Shape
from openglider.vector import Interpolation, PolyLine2D
from openglider.utils.table import Table


class ParametricShape(object):
    num_shape_interpolation = 50
    num_distribution_interpolation = 50
    num_depth_integral = 50
    baseline_pos = 0.25

    def __init__(self, front_curve, back_curve, rib_distribution, cell_num):
        self.front_curve = front_curve
        self.back_curve = back_curve
        self.rib_distribution = rib_distribution
        self.cell_num = cell_num

    def __json__(self):
        return {
            "front_curve": self.front_curve,
            "back_curve": self.back_curve,
            "rib_distribution": self.rib_distribution,
            "cell_num": self.cell_num,
        }

    def __repr__(self):
        return "{}\n\tcells: {}\n\tarea: {:.2f}\n\taspect_ratio: {:.2f}".format(
            super(ParametricShape, self).__repr__(),
            self.cell_num,
            self.area,
            self.aspect_ratio,
        )

    def copy(self):
        return self.__class__(
            self.front_curve.copy(),
            self.back_curve.copy(),
            self.rib_distribution.copy(),
            self.cell_num,
        )

    @property
    def baseline(self):
        return self.get_baseline(self.baseline_pos)

    def get_baseline(self, pct):
        shape = self.get_half_shape()
        line = []
        for i in range(shape.rib_no):
            line.append(shape.get_point(i, pct))

        return PolyLine2D(line)

    @property
    def has_center_cell(self):
        return self.cell_num % 2

    @property
    def half_cell_num(self):
        return self.cell_num // 2 + self.has_center_cell

    @property
    def half_rib_num(self):
        return self.half_cell_num + 1 - self.has_center_cell

    def rescale_curves(self):
        span = self.span

        dist_scale = span / self.rib_distribution.controlpoints[-1][0]
        self.rib_distribution.scale(dist_scale, 1)

        back_scale = span / self.back_curve.controlpoints[-1][0]
        self.back_curve.scale(back_scale, 1)

    @property
    def rib_dist_interpolation(self):
        """
        Interpolate Cell-distribution
        """
        data = self.rib_distribution.get_sequence(self.num_distribution_interpolation)
        interpolation = Interpolation([[p[1], p[0]] for p in data])
        start = self.has_center_cell / self.cell_num
        num = self.cell_num // 2 + 1
        return [[interpolation(i), i] for i in np.linspace(start, 1, num)]

    @property
    def fast_interpolation(self):
        data = self.rib_distribution.get_sequence(self.num_distribution_interpolation).T
        start = self.has_center_cell / self.cell_num
        num = self.cell_num // 2 + 1
        positions = np.linspace(start, 1, num)
        return np.array([np.interp(positions, data[1], data[0]), positions]).T

    # besser mit spezieller bezier?
    @property
    def rib_dist_controlpoints(self):
        return self.rib_distribution.controlpoints[1:-1]

    @rib_dist_controlpoints.setter
    def rib_dist_controlpoints(self, arr):
        x0 = self.front_curve.controlpoints[-1][0]
        self.rib_distribution.controlpoints = [[0, 0]] + arr + [[x0, 1]]

    @property
    def rib_x_values(self):
        return [p[0] for p in self.rib_dist_interpolation]

    @property
    def cell_x_values(self):
        ribs = self.rib_x_values
        if self.has_center_cell:
            ribs.insert(0, -ribs[0])

        cells = []
        for x1, x2 in zip(ribs[:-1], ribs[1:]):
            cells.append((x1 + x2) / 2)

        return cells

    def get_half_shape(self):
        """
        Return shape of the glider:
        [ribs, front, back]
        """
        num = self.num_shape_interpolation
        front_int = self.front_curve.interpolation(num=num)
        back_int = self.back_curve.interpolation(num=num)
        dist = self.rib_x_values
        front = [[x, front_int(x)] for x in dist]
        back = [[x, back_int(x)] for x in dist]

        return Shape(PolyLine2D(front), PolyLine2D(back))

    def get_shape(self):
        """
        Return shape of the glider:
        [ribs, front, back]
        """
        return self.get_half_shape().copy_complete()

    def __getitem__(self, pos):
        """if first argument is negative the point is returned mirrored"""
        rib_nr, rib_pos = pos
        ribs = self.ribs
        neg = rib_nr < 0
        sign = -neg * 2 + 1
        if rib_nr <= len(ribs):
            fr, ba = ribs[abs(rib_nr + neg * self.has_center_cell)]
            chord = ba[1] - fr[1]
            x = fr[0]
            y = fr[1] + rib_pos * chord
            return [sign * x, y]

    @property
    def ribs(self):
        return self.get_half_shape().ribs

    def get_rib_point(self, rib_no, x):
        ribs = list(self.ribs)
        if self.has_center_cell:
            ribs = [ribs[0] * np.array([-1, 1])] + list(ribs)
        rib = ribs[rib_no]
        return np.array([rib[0][0], rib[0][1] + x * (rib[1][1] - rib[0][1])])

    def get_shape_point(self, rib_no, x):
        k = rib_no % 1
        rib1 = int(rib_no)
        p1 = self.get_rib_point(rib1, x)

        if k > 0:
            p2 = self.get_rib_point(rib1 + 1, x)
            return p1 + k * (p2 - p1)
        else:
            return p1

    @property
    def depth_integrated(self):
        """
        Return A(x)
        """
        num = self.num_depth_integral
        x_values = np.linspace(0, self.span, num)
        front_int = self.front_curve.interpolation(num=num)
        back_int = self.back_curve.interpolation(num=num)
        integrated_depth = [0.0]
        for x in x_values[1:]:
            depth = front_int(x) - back_int(x)
            integrated_depth.append(integrated_depth[-1] + 1.0 / depth)
        y_values = [i / integrated_depth[-1] for i in integrated_depth]
        return zip(x_values, y_values)

    def set_const_cell_dist(self):
        const_dist = list(self.depth_integrated)
        num_pts = len(self.rib_distribution.controlpoints)
        self.rib_distribution.fit(const_dist, numpoints=num_pts)

    ############################################################################
    # scaling stuff
    def scale(self, x=1.0, y=None):
        if y is None:
            y = x
        self.front_curve.scale(x, y)

        # scale back to fit with front
        factor = self.front_curve[-1][0] / self.back_curve[-1][0]
        self.back_curve.scale(factor, y)

        # scale rib_dist
        factor = (
            self.front_curve.controlpoints[-1][0]
            / self.rib_distribution.controlpoints[-1][0]
        )
        self.rib_distribution.scale(factor, 1)

    @property
    def area(self):
        return self.get_shape().area

    def set_area(self, area, fixed="aspect_ratio"):
        if fixed == "aspect_ratio":
            # scale proportional
            factor = math.sqrt(area / self.area)
            self.scale(factor, factor)
        elif fixed == "span":
            # scale y
            factor = area / self.area
            self.scale(1, factor)
        elif fixed == "depth":
            # scale span
            factor = area / self.area
            self.scale(factor, 1)
        else:
            raise ValueError(
                "Invalid Value: {} for 'constant' (aspect_ratio, span, depth)".format(
                    fixed
                )
            )

        return self.area

    @property
    def aspect_ratio(self):
        # todo: span -> half span, area -> full area???
        return (2 * self.span) ** 2 / self.area

    def set_aspect_ratio(self, ar, fixed="span"):
        ar0 = self.aspect_ratio
        if fixed == "span":
            self.scale(y=ar0 / ar)
        elif fixed == "area":
            self.scale(x=np.sqrt(ar / ar0), y=np.sqrt(ar0 / ar))

    @property
    def span(self):
        span = self.front_curve.controlpoints[-1][0]
        return span

    @span.setter
    def span(self, span):
        factor = span / self.span
        self.scale(factor, 1)

    def set_span(self, span, fixed="area"):
        span_0 = self.span
        if fixed == "area":
            self.scale(x=span / span_0, y=span_0 / span)
        elif fixed == "aspect_ratio":
            self.scale(x=span / span_0, y=span / span_0)
        else:
            self.scale(x=span / span_0, y=1)
