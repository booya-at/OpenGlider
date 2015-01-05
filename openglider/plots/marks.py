import math

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


def line(p1, p2, rotation=False):
    if not rotation:
        return [PolyLine2D([p1, p2])]
    else:
        center = (p1+p2)/2
        rot = rotation_2d(rotation)
        return [PolyLine2D([center + rot.dot(p1-center), center+rot.dot(p2-center)])]


def cross(p1, p2, rotation=False):
    return line(p1, p2, rotation=rotation) + line(p1, p2, rotation=rotation+math.pi/2)




