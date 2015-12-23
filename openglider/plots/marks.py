import math
import numpy

from openglider.vector.functions import rotation_2d
from openglider.vector.polyline import PolyLine2D

scale = 0.8


def polygon(p1, p2, rotation=False, num=3, scale=scale, is_center=False):
    """Polygon"""
    if not is_center:
        center = (p1+p2)/2
    else:
        center = p1
    diff = (p2-center) * scale

    return [PolyLine2D([center + rotation_2d(math.pi*2*i/num+rotation).dot(diff) for i in range(num+1)])]


def triangle(p1, p2, scale=scale):
    return polygon(p1, p2, num=3, scale=scale)


def arrow_left(p1, p2, scale=1):
    d = (p2 - p1)*scale
    dr = numpy.array([-d[1], d[0]])/math.sqrt(2)

    return [PolyLine2D([p1, p1+d, p1+d/2+dr, p1])]


def arrow_right(p1, p2, scale=1):
    arrow = arrow_left(p1, p2, scale=scale)
    arrow[0].mirror(p1, p2)
    return arrow


def line(p1, p2, rotation=False):
    if not rotation:
        return [PolyLine2D([p1, p2])]
    else:
        center = (p1+p2)/2
        rot = rotation_2d(rotation)
        return [PolyLine2D([center + rot.dot(p1-center), center+rot.dot(p2-center)])]


def cross(p1, p2, rotation=False):
    return line(p1, p2, rotation=rotation) + line(p1, p2, rotation=rotation+math.pi/2)


def inside(fctn):
    """
    Put two profile points (outer, inner) on the inside of sewing mark
    :param fctn:
    :return:
    """
    return lambda p1, p2: fctn(2 * p1 - p2, p1)

class Modify():
    def __init__(self, func):
        self.func = func

    def __repr__(self):
        return "{} [{}]".format(self.__class__, repr(self.func))

    def __call__(self, p1, p2, *args, **kwargs):
        return self.func(p1, p2, *args, **kwargs)

class Rotate(Modify):
    def __init__(self, func, rotation):
        self.rotation = rotation
        super(Rotate, self).__init__(func)

    def __call__(self, *args, **kwargs):
        kwargs["rotation"] = self.rotation
        return super(Rotate, self).__call__(*args, **kwargs)

class OnLine(Modify):
    def __call__(self, p1, p2, *args, **kwargs):
        p1_2 = 0.5 * (p1+p2)
        p2_2 = 1.5 * p1 - 0.5 * p2
        return super(OnLine, self).__call__(p1_2, p2_2, *args, **kwargs)