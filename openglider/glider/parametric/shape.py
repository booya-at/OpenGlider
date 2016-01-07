from __future__ import division
import math
import numpy as np

from openglider.glider.shape import Shape
from openglider.vector import Interpolation, PolyLine2D


class ParametricShape(object):
    num_shape_interpolation = 50
    num_distribution_interpolation = 50

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
            "cell_num": self.cell_num
        }

    @property
    def span(self):
        span = self.front_curve.controlpoints[-1][0]

        return span

    @span.setter
    def span(self, span):
        factor = span/self.span
        self.scale(factor, 1)

    def scale(self, x=1., y=1.):
        self.front_curve.scale(x, y)

        # scale back to fit with front
        x_new = self.front_curve[-1][0] / self.back_curve[-1][0]
        self.back_curve.scale(x_new, y)

        # scale rib_dist
        factor = self.front_curve.controlpoints[-1][0] / self.rib_distribution.controlpoints[-1][0]
        self.rib_distribution.scale(factor, 1)

    @property
    def area(self):
        return self.get_shape().area

    def set_area(self, area, fixed="aspect_ratio"):
        if fixed == "aspect_ratio":
            # scale proportional
            factor = math.sqrt(area/self.area)
            self.scale(factor, factor)
        elif fixed == "span":
            # scale y
            factor = area/self.area
            self.scale(1, factor)
        elif fixed == "depth":
            # scale span
            factor = area/self.area
            self.scale(factor, 1)
        else:
            raise ValueError("Invalid Value: {} for 'constant' (aspect_ratio, span, depth)".format(fixed))

        return self.area

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
    def rib_x_values(self):
        return [p[0] for p in self.rib_dist_interpolation]

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

    @property
    def ribs(self):
        return self.get_half_shape().ribs

    def get_shape_point(self, rib_no, x):
        ribs = list(self.ribs)
        rib = ribs[rib_no]
        return rib[0][0], rib[0][1] + x * (rib[1][1] - rib[0][1])


