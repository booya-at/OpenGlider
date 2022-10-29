from __future__ import annotations

from abc import ABC
import math
from typing import Any, Dict, List, Sequence

import euklid

import openglider.vector.polygon as polygons

default_scale = 0.8

class Mark(ABC):
    def __repr__(self) -> str:
        return self.__class__.__name__
    
    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) ->  List[euklid.vector.PolyLine2D]:
        raise NotImplemented

class Empty(Mark):
    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        return []

class Combine(Mark):
    marks: Sequence[Mark]
    def __init__(self, *marks: Mark) -> None:
        self.marks = marks
    
    def __json__(self) -> Dict[str, Any]:
        return {"marks": self.marks}
    
    @classmethod
    def __from_json__(cls, marks) -> Combine:
        return cls(*marks)

    def __repr__(self) -> str:
        repr_self = self.__class__.__name__
        repr_children = ", ".join([str(x) for x in self.marks])
        return f"{repr_self} ({repr_children})"

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        result: List[euklid.vector.PolyLine2D] = []
        for mark in self.marks:
            result += mark(p1, p2)
        
        return result
            

class Polygon(Mark):
    def __init__(self, edges: int=3, scale: float=default_scale, name: str=""):
        self.scale = scale
        self.num_edges = edges
        self.name = name

    def __json__(self) -> Dict[str, Any]:
        return {"scale": self.scale, "edges": self.num_edges}

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        circle = polygons.Circle.from_p1_p2(p1, p2)

        return [circle.get_sequence(self.num_edges-1)]


class Triangle(Polygon):
    def __init__(self, scale: float=default_scale):
        super(Triangle, self).__init__(3, scale)

    def __json__(self) -> Dict[str, Any]:
        return {"scale": self.scale}


class Arrow(Mark):
    def __init__(self, left: bool=True, scale: float=default_scale, name: str=""):
        self.left = left
        self.scale = scale
        self.name = name

    def __json__(self) -> Dict[str, Any]:
        return {
            "left": self.left,
            "scale": self.scale
        }

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        d = (p2 - p1)*self.scale
        dr = euklid.vector.Vector2D([-d[1], d[0]])*(1/math.sqrt(2))
        if not self.left:
            dr *= -1.

        return [euklid.vector.PolyLine2D([
            p1,
            p1+d,
            p1+d*0.5+dr,
            p1
            ])]


class Line(Mark):
    def __init__(self, rotation: float=0., offset: float=0., name: str=""):
        self.rotation = rotation
        self.offset = offset
        self.name = name

    def __json__(self) -> Dict[str, Any]:
        return {
            "rotation": self.rotation,
            "offset": self.offset,
            "name": self.name
        }

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        if self.rotation:
            center = (p1+p2)*0.5
            rotation = euklid.vector.Rotation2D(self.rotation)
            return [euklid.vector.PolyLine2D([
                center + rotation.apply(p1-center),
                center + rotation.apply(p2-center)
                ])]
        else:
            return [euklid.vector.PolyLine2D([p1, p2])]


class Cross(Line):
    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        l1 = Line(rotation=self.rotation)
        l2 = Line(rotation=self.rotation+math.pi*0.5)
        return l1(p1, p2) + l2(p1, p2)


class Dot(Mark):
    position: List[float]
    def __init__(self, *positions: float):
        self.positions = positions

    def __json__(self) -> Dict[str, Any]:
        return {"positions": self.positions}
    
    @classmethod
    def __from_json__(cls, positions) -> Dot:
        return cls(*positions)

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        dots = []
        for x in self.positions:
            p = p1 + (p2 - p1) * x
            dots.append(p)
        return [euklid.vector.PolyLine2D([p]) for p in dots]


class _Modify(Mark):
    def __init__(self, func: Mark):
        self.func = func

    def __json__(self) -> Dict[str, Any]:
        return {"func": self.func}

    def __repr__(self) -> str:
        return "{}->{}".format(self.__class__.__name__, repr(self.func))

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        return self.func(p1, p2)


class Rotate(_Modify):
    def __init__(self, func: Mark, rotation: float, center: bool=True):
        self.angle = rotation
        self.rotation = euklid.vector.Rotation2D(rotation)
        super(Rotate, self).__init__(func)
    
    def __deepcopy__(self, memo: Any) -> Rotate:
        return Rotate(self.func, self.angle)

    def __json__(self) -> Dict[str, Any]:
        return {"func": self.func,
                "rotation": self.angle}

    def __repr__(self) -> str:
        return "Rotate({})->{}".format(self.angle, self.func)

    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        diff = (p2 - p1) * 0.5
        center = (p1 + p2) * 0.5
        diff_new = self.rotation.apply(diff)

        p1_new, p2_new = center + diff_new, center - diff_new
        return super().__call__(p1_new, p2_new)


class OnLine(_Modify):
    """
    Modify Mark to sit centered on p2 rather than in between
    |x|  <- old
    | |
    | x  <- new
    | |
    """
    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        p1_2 = (p1+p2) * 0.5
        p2_2 = p1 * 1.5 - p2 * 0.5
        return super(OnLine, self).__call__(p1_2, p2_2)


class Inside(_Modify):
    """
    Modify Mark to be on the other side (inside)
    |x|   <- old
    | |
    | |x  <- new
    l1|
      | l2
    """
    def __call__(self, p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> List[euklid.vector.PolyLine2D]:
        p1_2 = p1*2-p2
        p2_2 = p1
        return super(Inside, self).__call__(p1_2, p2_2)