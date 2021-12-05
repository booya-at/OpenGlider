import logging
import math
from typing import List, TYPE_CHECKING

import euklid
import numpy as np
import openglider
from openglider.glider.shape import Shape
from openglider.lines import Node
from openglider.utils.dataclass import dataclass
from openglider.vector.polygon import Circle, Ellipse

if TYPE_CHECKING:
    from openglider.glider.glider import Glider
    from openglider.glider.rib.rib import Rib

logger = logging.getLogger(__name__)


class RibHoleBase:
    def get_curves(self, rib: "Rib", num: int) -> List[euklid.vector.PolyLine2D]:
        raise NotImplementedError()

    def get_centers(self, rib: "Rib", scale=False) -> List[euklid.vector.Vector2D]:
        raise NotImplementedError()
    
    def get_3d(self, rib: "Rib", num: int=20):
        hole = self.get_curves(rib, num=num)
        return [rib.align_all(c) for c in hole]

    def get_flattened(self, rib: "Rib", num: int=80, scale=True):
        points = self.get_curves(rib, num)
        if scale:
            points = [l.scale(rib.chord) for l in points]
        
        return points


@dataclass
class RibHole(RibHoleBase):
    """
    Round holes.
    height is relative to profile height, rotation is from lower point
    """
    pos: float
    size: float=0.5
    width: float=1
    vertical_shift: float=0
    rotation: float=0

    def __init__(self, pos, size=0.5, width=1, vertical_shift=0., rotation=0.):
        self.pos = pos
        if isinstance(size, (list, tuple, np.ndarray, euklid.vector.Vector2D)):
            # TODO: modernize
            width = size[0]/size[1]
            self.size = size[1]
        else:
            self.size = size
        self.vertical_shift = vertical_shift
        self.rotation = rotation  # rotation around lower point
        self.width = width

    def get_curves(self, rib: "Rib", num=80) -> List[euklid.vector.PolyLine2D]:
        lower = rib.profile_2d.get(self.pos)
        upper = rib.profile_2d.get(-self.pos)

        diff = upper - lower
        if self.rotation:
            diff = euklid.vector.Rotation2D(self.rotation).apply(diff)
        
        center = lower + diff * (0.5 + self.vertical_shift/2)
        outer_point = center + diff*self.size/2

        circle = Ellipse.from_center_p2(center, outer_point, self.width)

        return [circle.get_sequence(num)]
    
    def get_centers(self, rib: "Rib", scale=False) -> List[euklid.vector.Vector2D]:
        # TODO: remove and use a polygon.centerpoint
        lower = rib.profile_2d.get(self.pos)
        upper = rib.profile_2d.get(-self.pos)

        diff = upper - lower
        if self.rotation:
            diff = euklid.vector.Rotation2D(self.rotation).apply(diff)
        
        return [lower + diff * (0.5 + self.vertical_shift/2)]


@dataclass
class RibSquareHole(RibHoleBase):
    x: float
    width: float
    height: float
    corner_size: float = 0.9

    def get_centers(self, rib: "Rib", scale=False) -> List[euklid.vector.Vector2D]:
        return [rib.profile_2d.align([self.x, 0])]

    def get_curves(self, rib: "Rib", num=80) -> List[euklid.vector.PolyLine2D]:
        x1 = self.x - self.width/2
        x2 = self.x + self.width/2

        # y -> [-1, 1]
        corner_height = (1-self.corner_size) * self.height
        corner_width = (1-self.corner_size) * self.width/2        

        controlpoints = [
            [x1, 0],
            [x1, corner_height],
            [x1, self.height],
            [self.x - corner_width, self.height],
            [self.x, self.height],
            [self.x + corner_width, self.height],
            [x2, self.height],
            [x2, corner_height],
            [x2, 0],
            [x2, -corner_height],
            [x2, -self.height],
            [self.x + corner_width, -self.height],
            [self.x, -self.height],
            [self.x - corner_width, -self.height],
            [x1, -self.height],
            [x1, -corner_height],
            [x1, 0]
        ]

        curve = euklid.spline.BSplineCurve([rib.profile_2d.align(p) for p in controlpoints])

        return [curve.get_sequence(num)]

@dataclass
class MultiSquareHole(RibHoleBase):
    start: float
    end: float
    height: float
    num_holes: int
    border_width: float

    @property
    def total_border(self) -> float:
        return (self.num_holes-1) * self.border_width

    @property
    def hole_width(self):

        width = (self.end - self.start - self.total_border) / self.num_holes
        if width < 1e-5:
            raise ValueError(f"Cannot fit {self.num_holes} with border: {self.border_width}")

        return width
    
    @property
    def hole_x_values(self):
        hole_width = self.hole_width

        x = self.start + hole_width/2

        return [x + i*(hole_width+self.border_width) for i in range(self.num_holes)]
    
    def get_centers(self, rib: "Rib", scale: bool=False) -> List[euklid.vector.Vector2D]:
        return [rib.profile_2d.align([x, 0]) for x in self.hole_x_values]
    
    def get_curves(self, rib: "Rib", num: int=80) -> List[euklid.vector.PolyLine2D]:
        hole_width = self.hole_width

        curves = []
        for center in self.hole_x_values:
            hole = RibSquareHole(center, hole_width, self.height)

            curves += hole.get_curves(rib, num)
        
        return curves
