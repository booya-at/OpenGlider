from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import euklid
import pyfoil

from openglider.mesh import Mesh
from openglider.utils.cache import cached_function
from openglider.utils.dataclass import BaseModel
from openglider.vector.drawing import PlotPart
from openglider.vector.polygon import Ellipse
from openglider.vector.unit import Angle, Length, Percentage

if TYPE_CHECKING:
    from openglider.glider.rib.rib import Rib

logger = logging.getLogger(__name__)


class RibHoleBase(BaseModel):
    name: str = "unnamed"
    margin: Percentage | Length= Percentage("2%")

    def get_envelope_airfoil(self, rib: Rib) -> pyfoil.Airfoil:
        return rib.get_offset_outline(self.margin)
    
    @cached_function("margin")
    def get_envelope_boundaries(self, rib: Rib) -> tuple[Percentage, Percentage]:
        envelope = self.get_envelope_airfoil(rib)
        x2 = envelope.curve.nodes[0][0]
        x1 = min([p[0] for p in envelope.curve.nodes])

        return Percentage(x1), Percentage(x2)
    
    def align_contolpoints(self, controlpoints: list[euklid.vector.Vector2D], rib: Rib) -> list[euklid.vector.Vector2D]:
        envelope = self.get_envelope_airfoil(rib)
        return [envelope.align(cp) for cp in controlpoints]

    def _get_curves(self, rib: Rib, num: int) -> list[euklid.vector.PolyLine2D]:
        raise NotImplementedError()
    
    def get_curves(self, rib: Rib, num: int=80, scale: bool=False) -> list[euklid.vector.PolyLine2D]:
        curves = self._get_curves(rib, num)

        if scale:
            return [line.scale(rib.chord) for line in curves]
        else:
            return curves

    def get_centers(self, rib: Rib, scale: bool=False) -> list[euklid.vector.Vector2D]:
        raise NotImplementedError()
    
    def get_3d(self, rib: Rib, num: int=20) -> list[euklid.vector.PolyLine3D]:
        hole = self.get_curves(rib, num=num)
        return [rib.align_all(c) for c in hole]

    def get_flattened(self, rib: Rib, num: int=80, layer_name: str="cuts") -> PlotPart:
        curves = [l.scale(rib.chord) for l in self.get_curves(rib, num)]
        
        pp = PlotPart()
        pp.layers[layer_name] += curves
        return pp
    
    def get_parts(self, rib: Rib) -> list[PlotPart]:
        return []
    
    def get_mesh(self, rib: Rib) -> Mesh | None:
        return None


class RibHole(RibHoleBase):
    """
    Round holes.
    height is relative to profile height, rotation is from lower point
    """
    pos: Percentage
    size: Percentage=Percentage(0.5)
    width: Percentage=Percentage(1.)

    vertical_shift: Percentage=Percentage(0)
    rotation: Angle=Angle(0)

    def _get_points(self, rib: Rib) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        lower = rib.profile_2d.get(self.pos.si)
        upper = rib.profile_2d.get(-self.pos.si)

        diff = upper - lower
        if self.rotation:
            diff = euklid.vector.Rotation2D(self.rotation.si).apply(diff)

        center = lower + diff * (0.5 + self.vertical_shift.si/2)
        outer_point = center + diff.normalized() * self.get_diameter(rib)/2

        return center, outer_point

    def _get_curves(self, rib: Rib, num: int=80) -> list[euklid.vector.PolyLine2D]:
        center, outer_point = self._get_points(rib)
        
        circle = Ellipse.from_center_p2(center, outer_point, self.width.si)

        return [circle.get_sequence(num)]
    
    def get_diameter(self, rib: Rib) -> float:
        lower = rib.profile_2d.get(self.pos.si)
        upper = rib.profile_2d.get(-self.pos.si)

        diff = upper - lower
        
        return diff.length() * self.size.si
    
    def get_centers(self, rib: Rib, scale: bool=False) -> list[euklid.vector.Vector2D]:
        return [self._get_points(rib)[0]]


class PolygonHole(RibHoleBase):
    points: list[euklid.vector.Vector2D]
    corner_size: float=1

    class Config:
        arbitrary_types_allowed = True

    def get_centers(self, rib: Rib, scale: bool=False) -> list[euklid.vector.Vector2D]:
        centers = [sum(self.points, start=euklid.vector.Vector2D())/len(self.points)]

        if scale:
            return [p * rib.chord for p in centers]
        
        return centers

    def _get_curves(self, rib: Rib, num: int=160) -> list[euklid.vector.PolyLine2D]:
        segments = []

        def get_point(index: int) -> euklid.vector.Vector2D:
            if index >= len(self.points):
                index -= len(self.points)
            
            return self.points[index]

        for i in range(len(self.points)):
            p1 = get_point(i)
            p2 = get_point(i+1)
            p3 = get_point(i+2)

            segments.append([
                p1 + (p2-p1) * (1-self.corner_size/2),
                p2,
                p2 + (p3-p2) * (self.corner_size/2)
            ])

        sequence = []
        for i, segment in enumerate(segments):
            sequence += euklid.spline.BSplineCurve(segment).get_sequence(num).nodes

            if self.corner_size < 1:
                if i+1 >= len(segments):
                    segment2 = segments[0]
                else:
                    segment2 = segments[i+1]
                
                sequence += [segment[-1], segment2[0]]

        return [euklid.vector.PolyLine2D(sequence).resample(num)]


class RibSquareHole(RibHoleBase):
    x: Percentage
    width: Percentage | Length
    height: Percentage
    corner_size: float = 1        

    def get_centers(self, rib: Rib, scale: bool=False) -> list[euklid.vector.Vector2D]:
        width = rib.convert_to_percentage(self.width)

        x1 = self.x - width/2
        x2 = self.x + width/2

        xmin, xmax = self.get_envelope_boundaries(rib)
        if x1 < xmin or x2 > xmax:
            return []
        
        centers = [rib.profile_2d.align([self.x, 0])]
        
        if scale:
            return [p * rib.chord for p in centers]
        
        return centers
    
    def _get_curves(self, rib: Rib, num: int=80) -> list[euklid.vector.PolyLine2D]:
        width = rib.convert_to_percentage(self.width)
        x1 = self.x - width/2
        x2 = self.x + width/2

        xmin, xmax = self.get_envelope_boundaries(rib)
        if x1 < xmin or x2 > xmax:
            return []
        
        p1, p2, p3, p4 = self.align_contolpoints([
            euklid.vector.Vector2D([x1, -self.height]),
            euklid.vector.Vector2D([x2, -self.height]),
            euklid.vector.Vector2D([x2, self.height]),
            euklid.vector.Vector2D([x1, self.height])
        ], rib)

        return PolygonHole(points=[p1, p2, p3, p4]).get_curves(rib, num)


class MultiSquareHole(RibHoleBase):
    start: Percentage
    end: Percentage
    height: Percentage
    num_holes: int
    border_width: Percentage | Length

    @property
    def total_border(self) -> Percentage | Length:
        return (self.num_holes-1) * self.border_width

    def hole_width(self, rib: Rib) -> Percentage:
        total_border = rib.convert_to_percentage(self.total_border)

        width = (self.end - self.start - total_border) / self.num_holes
        if width < 1e-5:
            raise ValueError(f"Cannot fit {self.num_holes} with border: {self.border_width}")

        return width
    
    def hole_x_values(self, rib: Rib) -> list[Percentage]:
        hole_width = self.hole_width(rib)

        x = self.start + hole_width/2

        return [x + i*(hole_width+self.border_width) for i in range(self.num_holes)]
    
    def _get_holes(self, rib: Rib) -> list[RibSquareHole]:
        hole_width = self.hole_width(rib)
        holes = []
        for center in self.hole_x_values(rib):
            holes.append(RibSquareHole(x=center, width=hole_width, height=self.height, margin=self.margin))

        return holes
    
    def get_centers(self, rib: Rib, scale: bool=False) -> list[euklid.vector.Vector2D]:
        holes = []
        for hole in self._get_holes(rib):
            holes += hole.get_centers(rib, scale=scale)
        
        return holes
    
    def _get_curves(self, rib: Rib, num: int=80) -> list[euklid.vector.PolyLine2D]:
        curves = []
        for hole in self._get_holes(rib):
            curves += hole.get_curves(rib, num)
        
        return curves


class AttachmentPointHole(RibHoleBase):
    start: Percentage
    end: Percentage

    num_holes: int
    border: Length | Percentage=Length(0.1)
    side_border: Length | Percentage=Length(0.1)
    corner_size: Percentage = Percentage(1.)

    @cached_function('self')
    def _get_holes(self, rib: Rib) -> list[PolygonHole]:
        envelope = self.get_envelope_airfoil(rib)

        p1 = envelope.align([self.start, -1])
        p2 = envelope.align([(self.start+self.end)/2, 1])
        p3 = envelope.align([self.end, -1])

        upper = euklid.vector.Interpolation([p1, p2, p3])
        lower = euklid.vector.Interpolation([p1, p3])

        side_border_pct = rib.convert_to_percentage(self.side_border)
        border_pct = rib.convert_to_percentage(self.border)

        total_border_pct = (2*side_border_pct + (self.num_holes-1)*border_pct)

        hole_width  = (Percentage(float(abs(self.start-self.end))) - total_border_pct)/self.num_holes

        if hole_width < 0:
            raise ValueError(f"not enough space for {self.num_holes} holes between {self.start} / {self.end} ({rib.name})")

        holes = []

        for hole_no in range(self.num_holes):
            left = self.start + side_border_pct + hole_no*border_pct + hole_no*hole_width
            right = left + hole_width

            p1 = euklid.vector.Vector2D([left, lower.get_value(left.si)])
            p2 = euklid.vector.Vector2D([right, lower.get_value(right.si)])
            
            p4 = euklid.vector.Vector2D([left, upper.get_value(left.si)])
            p3 = euklid.vector.Vector2D([right, upper.get_value(right.si)])

            holes.append(PolygonHole(points=[p1, p2, p3, p4], corner_size=self.corner_size.si))
        
        return holes

    def _get_curves(self, rib: Rib, num: int=80) -> list[euklid.vector.PolyLine2D]:
        curves = []
        for hole in self._get_holes(rib):
            curves += hole.get_curves(rib, num)
        
        return curves

    def get_centers(self, rib: Rib, scale: bool=False) -> list[euklid.vector.Vector2D]:
        holes = []
        for hole in self._get_holes(rib):
            holes += hole.get_centers(rib, scale=scale)
        
        return holes
