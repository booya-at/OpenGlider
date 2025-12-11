import math
import numpy as np

from openglider.vector.functions import rotation_2d
from openglider.vector.polyline import PolyLine2D
from openglider.vector.transformation import Translation, Scale, Rotation

default_scale = 0.8


class Mark(object):
    def __repr__(self):
        return self.__class__.__name__


class Polygon(Mark):
    def __init__(self, edges=3, scale=default_scale, name=None):
        self.scale = scale
        self.num_edges = edges
        self.name = name

    def __json__(self):
        return {"scale": self.scale, "edges": self.num_edges}

    def __call__(self, p1, p2):
        center = (p1 + p2) / 2
        diff = self.scale * (p2 - center)
        points = [
            center + rotation_2d(math.pi * 2 * i / self.num_edges).dot(diff)
            for i in range(self.num_edges + 1)
        ]
        # points = np.array(points) * self.scale
        return [PolyLine2D(points, name=self.name)]


class Triangle(Polygon):
    def __init__(self, scale=default_scale):
        super(Triangle, self).__init__(3, scale)

    def __json__(self):
        return {"scale": self.scale}


class Arrow(Mark):
    def __init__(self, left=True, scale=default_scale, name=None):
        self.left = left
        self.scale = scale
        self.name = name

    def __json__(self):
        return {"left": self.left, "scale": self.scale}

    def __call__(self, p1, p2):
        d = (p2 - p1) * self.scale
        dr = np.array([-d[1], d[0]]) / math.sqrt(2)
        if not self.left:
            dr = -dr

        return [PolyLine2D([p1, p1 + d, p1 + d / 2 + dr, p1], name=self.name)]


class Line(Mark):
    def __init__(self, rotation=0.0, offset=0.0, name=None):
        self.rotation = rotation
        self.offset = offset
        self.name = name

    def __json__(self):
        return {"rotation": self.rotation, "offset": self.offset, "name": self.name}

    def __call__(self, p1, p2):
        if self.rotation:
            center = (p1 + p2) / 2
            rot = rotation_2d(self.rotation)
            return [
                PolyLine2D(
                    [center + rot.dot(p1 - center), center + rot.dot(p2 - center)],
                    name=self.name,
                )
            ]
        else:
            return [PolyLine2D([p1, p2], name=self.name)]


class Cross(Line):
    def __call__(self, p1, p2):
        l1 = Line(rotation=self.rotation)
        l2 = Line(rotation=self.rotation + math.pi / 2)
        return l1(p1, p2) + l2(p1, p2)


class Dot(Mark):
    def __init__(self, *positions):
        self.positions = positions

    def __json__(self):
        return {"pos": self.positions}

    def __call__(self, p1, p2):
        dots = []
        for x in self.positions:
            p = p1 + x * (p2 - p1)
            dots.append(p)
        return [PolyLine2D([p]) for p in dots]


class _Modify(Mark):
    def __init__(self, func):
        self.func = func

    def __json__(self):
        return {"func": self.func}

    def __repr__(self):
        return "{}->{}".format(self.__class__.__name__, repr(self.func))

    def __call__(self, p1, p2, *args, **kwargs):
        return self.func(p1, p2, *args, **kwargs)


class Rotate(_Modify):
    def __init__(self, func, rotation, center=True):
        self.angle = rotation
        self.rotation = rotation_2d(rotation)
        super(Rotate, self).__init__(func)

    def __json__(self):
        return {"func": self.func, "rotation": self.angle}

    def __repr__(self):
        return "Rotate({})->{}".format(self.angle, self.func)

    def __call__(self, p1, p2):
        diff = (p2 - p1) / 2
        center = (p1 + p2) / 2
        diff_new = self.rotation.dot(diff)

        p1_new, p2_new = center + diff_new, center - diff_new
        return super(Rotate, self).__call__(p1_new, p2_new)


class OnLine(_Modify):
    """
    Modify Mark to sit centered on p2 rather than in between
    |x|  <- old
    | |
    | x  <- new
    | |
    """

    def __call__(self, p1, p2, *args, **kwargs):
        p1_2 = 0.5 * (p1 + p2)
        p2_2 = 1.5 * p1 - 0.5 * p2
        return super(OnLine, self).__call__(p1_2, p2_2, *args, **kwargs)


class Inside(_Modify):
    """
    Modify Mark to be on the other side (inside)
    |x|   <- old
    | |
    | |x  <- new
    l1|
      | l2
    """

    def __call__(self, p1, p2, *args, **kwargs):
        p1_2 = 2 * p1 - p2
        p2_2 = p1
        return super(Inside, self).__call__(p1_2, p2_2, *args, **kwargs)
