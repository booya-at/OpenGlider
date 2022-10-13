from __future__ import annotations

import numpy
import euklid
import math

V2 = euklid.vector.Vector2D

class CirclePart(object):
    """
    "A piece of the cake"
    
       /) <-- p1
      /   )
     /     )
    X       ) <-- p2
     \     )
      \   )
       \) <-- p3
    """
    def __init__(self, p1: V2, p2: V2, p3: V2):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

        l1 = p2 - p1
        l2 = p3 - p2

        rotation = euklid.vector.Rotation2D(-math.pi/2)

        n1 = rotation.apply(l1)
        n2 = rotation.apply(l2)

        p12 = (p1 + p2)/2
        p23 = (p2 + p3)/2

        cut_result: euklid.vector.CutResult = euklid.vector.cut(p12, p12+n1, p23, p23+n2)

        self.center = cut_result.point
        self.r: euklid.vector.Vector2D = p1 - self.center

    def get_sequence(self, num: int=20) -> euklid.vector.PolyLine2D:
        lst = []

        end = self.r.angle() - (self.p3-self.center).angle()
        
        for angle in numpy.linspace(0, end, num):
            lst.append(self.center + euklid.vector.Rotation2D(-angle).apply(self.r))

        return euklid.vector.PolyLine2D(lst)

    def _repr_svg_(self) -> str:

        svg = "<svg>"
        def point(p: V2, color: str="red") -> str:
            return '<circle cx="{}" cy="{}" r="1" stroke="{}" fill="transparent" stroke-width="5"/>'.format(p[0], p[1], color)

        svg += point(self.center, "blue")


        svg += point(self.p1)
        svg += point(self.p2)
        svg += point(self.p3)

        svg += "</svg>"
        return svg


class Ellipse(object):
    def __init__(self, center: V2, radius: float, height: float, rotation: float=0.):
        self.center = center
        self.radius = radius
        self.height = height
        self.rotation = rotation

    def get_sequence(self, num: int=20) -> euklid.vector.PolyLine2D:
        points = []

        for i in range(num):
            angle = math.pi * 2 * (i/(num-1))
            diff = euklid.vector.Vector2D([math.cos(angle), self.height*math.sin(angle)]) * self.radius
            
            points.append(self.center + diff)

        line = euklid.vector.PolyLine2D(points)

        return line.rotate(self.rotation, self.center)

    @classmethod
    def from_center_p2(cls, center: V2, p2: V2, aspect_ratio: float=1.) -> Ellipse:
        diff = p2 - center
        radius = diff.length()
        diff_0 = diff.normalized()

        rotation = math.atan2(diff_0[1], diff_0[0])

        return cls(center, radius, aspect_ratio, rotation)


class Circle(Ellipse):
    def __init__(self, center: V2, radius: float, rotation: float=0.):
        super().__init__(center, radius, radius, rotation)
    
    @classmethod
    def from_p1_p2(cls, p1: V2, p2: V2) -> Circle:
        center = (p1 + p2)*0.5
        radius = (p2-p1).length() * 0.5
        return cls(center, radius)