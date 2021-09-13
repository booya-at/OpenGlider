from typing import Optional

import euklid

from openglider.glider.shape import Shape
from openglider.utils.cache import cached_property

class Curve:
    upper = False
    def __init__(self, points, shape: Optional[Shape]=None):
        self.interpolation = euklid.vector.Interpolation(points)
        self.shape = shape

    @property
    def controlpoints(self):
        return self.interpolation.nodes
    
    @controlpoints.setter
    def controlpoints(self, points):
        self.interpolation.nodes = points
    
    def get(self, rib_no: int):
        if rib_no == 0 and self.shape.has_center_cell:
            rib_no = 1

        y = self.interpolation.get_value(rib_no)

        if self.upper:
            y = -y

        return y
        
    def draw(self) -> euklid.vector.PolyLine2D:
        x_values = [p[0] for p in self.controlpoints]

        start = min(x_values)
        end = max(x_values)

        start_int = int(start) + (start % 1) > 1e-10

        x_values_lst = list(range(start_int, int(end)))

        if start % 1:
            x_values_lst.insert(0, start)
        
        if end % 1:
            x_values_lst.append(end)
        
        return euklid.vector.PolyLine2D([self.shape.get_point(x, self.get(x)) for x in x_values_lst])



class ShapeCurve(Curve):
    @cached_property('shape', 'interpolation')
    def points_2d(self) -> euklid.vector.PolyLine2D:
        print("jooo")
        return euklid.vector.PolyLine2D([
            euklid.vector.Vector2D(self.shape.get_point(*p)) for p in self.interpolation.nodes
        ])
    
    def get(self, rib_no: int):
        if rib_no == 0 and self.shape.has_center_cell:
            rib_no = 1

        front, back = self.shape.front.get(rib_no), self.shape.back.get(rib_no)

        results = self.points_2d.cut(front, back)

        if len(results) != 1:
            raise Exception(f"wrong number of cut results: {len(results)}")

        return results[0][1]


class ShapeBSplineCurve(ShapeCurve):
    curve_cls = euklid.spline.BSplineCurve

    def __init__(self, points, shape: Shape, curve_cls=None):
        if curve_cls is not None:
            self.curve_cls = curve_cls
        
        super().__init__(points, shape)
    
    @cached_property('shape', 'interpolation')
    def points_2d(self) -> euklid.vector.PolyLine2D:
        return euklid.spline.BSplineCurve([
            euklid.vector.Vector2D(self.shape.get_point(*p)) for p in self.controlpoints
        ]).get_sequence(100)
