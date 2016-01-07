import math

from openglider.glider.shape import Shape


class ParametricShape(object):
    def __init__(self, front, back, cell_dist):
        self.front_curve = front
        self.back_curve = back
        self.cell_distribution = cell_dist

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

    @property
    def area(self):
        return 0

    def set_area(self, area, constant="aspect_ratio"):
        if constant == "aspect_ratio":
            # scale proportional
            factor = math.sqrt(area/self.area)
            self.scale(factor, factor)
        elif constant == "span":
            # scale y
            factor = area/self.area
            self.scale(1, factor)
        else:
            # scale span
            factor = area/self.area
            self.scale(factor, 1)

        return self.area



