from __future__ import annotations
import copy
from typing import Any, Dict, List, Tuple

import euklid

from openglider.glider.ballooning.base import BallooningBase
from openglider.utils.types import CurveType


class Ballooning(BallooningBase):

    def __init__(self, f_upper: euklid.vector.Interpolation, f_lower: euklid.vector.Interpolation):
        self.upper: euklid.vector.Interpolation = f_upper
        self.lower: euklid.vector.Interpolation = f_lower

    def __json__(self) -> dict[str, Any]:
        return {'f_upper': self.upper,
                'f_lower': self.lower}

    def __getitem__(self, xval: float) -> float:
        """Get Ballooning Value (%) for a certain XValue"""
        if -1 <= xval < 0:
            #return self.upper.xpoint(-xval)[1]
            return self.upper.get_value(-xval)
        elif 0 <= xval <= 1:
            #return -self.lower.xpoint(xval)[1]
            return self.lower.get_value(xval)
        else:
            raise ValueError(f"Value {xval} not between -1 and 1")

    def __add__(self, other: BallooningBase) -> BallooningBase:
        """Add another Ballooning to this one, needed for merging purposes"""
        if not isinstance(other, Ballooning):
            raise NotImplementedError()

        upper = []
        for point in self.upper.nodes:
            upper.append([point[0], point[1]+other.upper.get_value(point[0])])
        lower = []
        for point in self.lower.nodes:
            lower.append([point[0], point[1]+other.lower.get_value(point[0])])

        return Ballooning(
            euklid.vector.Interpolation(upper, extrapolate=True), 
            euklid.vector.Interpolation(lower, extrapolate=True)
            )

    def __imul__(self, val: float) -> Ballooning:
        for point in self.upper.nodes:
            point[1] *= val
        for point in self.lower.nodes:
            point[1] *= val
        return self

    def __mul__(self, value: float) -> Ballooning:
        """Multiply Ballooning With a Value"""
        new = self.copy()
        new *= value
        return new

    def copy(self) -> Ballooning:
        return copy.deepcopy(self)

    def mapx(self, xvals: list[float]) -> list[float]:
        return [self[i] for i in xvals]

    @property
    def amount_maximal(self) -> float:
        return max(max([p[1] for p in self.upper]), max([p[1] for p in self.lower]))

    @amount_maximal.setter
    def amount_maximal(self, amount: float) -> None:
        factor = float(amount) / self.amount_maximal
        self.scale(factor)

    @property
    def amount_integral(self) -> float:
        # Integration of 2-points always:
        amount = 0.
        for curve in [self.upper, self.lower]:
            for p1, p2 in zip(curve.nodes[:-1], curve.nodes[1:]):
                # points: (x1,y1), (x2,y2)
                #     _ p2
                # p1_/ |
                #  |   |
                #  |___|
                amount += (p1[1] + (p2[1]-p1[1])/2) * (p2[0]-p1[0])
        return amount / 2

    def scale(self, factor: float) -> None:
        self.upper.scale(euklid.vector.Vector2D([1, factor]))
        self.lower.scale(euklid.vector.Vector2D([1, factor]))

    def close_trailing_edge(self, start_x: float) -> None:
        def close(curve: euklid.vector.Interpolation) -> euklid.vector.Interpolation:
            new_nodes = []
            for p in curve.nodes:
                x = p[0]
                y = p[1]
                if x > start_x:
                    # t_e_c -> 1
                    # 1 -> 0
                    # steigung = 1/(1-t_e_c)
                    # d = 1
                    t_e_c = start_x
                    y = y * (1 - (x-t_e_c)/(1-t_e_c))
                    #y = (1-x) * y
                
                new_nodes.append([x, y])
            
            return euklid.vector.Interpolation(new_nodes)
        
        self.upper = close(self.upper)
        self.lower = close(self.lower)

    def _repr_svg_(self) -> str:
        import svgwrite
        import svgwrite.container

        height = self.amount_maximal * 2

        drawing = svgwrite.Drawing(size=[800, 800*height])

        drawing.viewbox(0, -height/2, 1, height)

        g = svgwrite.container.Group()
        g.scale(1, -1)
        upper = drawing.polyline(self.upper.nodes, style="stroke:black; vector-effect: non-scaling-stroke; fill: none;")
        lower = drawing.polyline([(p[0], -p[1]) for p in self.lower.nodes], style="stroke:black; vector-effect: non-scaling-stroke; fill: none;")
        g.add(upper)
        g.add(lower)
        drawing.add(g)

        return drawing.tostring()


class BallooningBezier(Ballooning):
    num_points = 100
    def __init__(self, upper: list[euklid.vector.Vector2D]=None, lower: list[euklid.vector.Vector2D]=None, name: str="ballooning") -> None:
        super().__init__(None, None)  # type: ignore
        upper = upper or euklid.vector.PolyLine2D([[0, 0], [0.1, 0], [0.2, 0.14], [0.8, 0.14], [0.9, 0], [1, 0]]).nodes
        lower = lower or euklid.vector.PolyLine2D([[0, 0], [0.1, 0], [0.2, 0.14], [0.8, 0.14], [0.9, 0], [1, 0]]).nodes

        self.upper_spline = euklid.spline.BSplineCurve(upper)
        self.lower_spline = euklid.spline.BSplineCurve(lower)

        self.upper_spline.controlpoints.nodes[0][0] = 0
        self.upper_spline.controlpoints.nodes[-1][0] = 1
        self.lower_spline.controlpoints.nodes[0][0] = 0
        self.lower_spline.controlpoints.nodes[-1][0] = 1
        
        self.name = name
        self.apply_splines()

    def __json__(self) -> dict[str, Any]:
        return {"upper": [list(p) for p in self.upper_spline.controlpoints],
                "lower": [list(p) for p in self.lower_spline.controlpoints]}

    @property
    def points(self) -> euklid.vector.PolyLine2D:
        upper = self.upper_spline.get_sequence(self.num_points).nodes
        lower = self.lower_spline.get_sequence(self.num_points).reverse() * euklid.vector.Vector2D([1., -1.])

        return euklid.vector.PolyLine2D(upper + lower.nodes)

    def get_points(self, n: int=150) -> list[euklid.vector.Vector2D]:
        n_2 = int(n / 2)

        upper = self.upper_spline.get_sequence(n_2).reverse() * euklid.vector.Vector2D([-1., 1.])
        lower = self.lower_spline.get_sequence(self.num_points)
        return upper.nodes + lower.nodes

    def apply_splines(self) -> None:
        self.upper = euklid.vector.Interpolation(self.upper_spline.get_sequence(self.num_points).nodes, extrapolate=True)
        self.lower = euklid.vector.Interpolation(self.lower_spline.get_sequence(self.num_points).nodes, extrapolate=True)

    def __imul__(self, factor: float) -> BallooningBezier:  # TODO: Check consistency
        """Multiplication of BezierBallooning"""
        # Multiplicate as normal interpolated ballooning, then refit
        #Ballooning.__imul__(self, factor)
        #self.upper_spline.fit(self.upper.data)
        #self.lower_spline.fit(self.lower.data)
        scale = euklid.vector.Vector2D([1, factor])
        self.controlpoints = (
            self.controlpoints[0] * scale,
            self.controlpoints[1] * scale
        )
        
        return self

    @property
    def numpoints(self) -> int:
        return len(self.upper)

    @numpoints.setter
    def numpoints(self, numpoints: int) -> None:
        upper = self.upper_spline.get_sequence(numpoints)
        lower = self.lower_spline.get_sequence(numpoints)
        Ballooning.__init__(self, euklid.vector.Interpolation(upper.nodes), euklid.vector.Interpolation(lower.nodes))

    @property
    def controlpoints(self) -> tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]:
        return self.upper_spline.controlpoints, self.lower_spline.controlpoints

    @controlpoints.setter
    def controlpoints(self, controlpoints: tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]) -> None:
        upper, lower = controlpoints
        if upper is not None:
            self.upper_spline.controlpoints = upper
        if lower is not None:
            self.lower_spline.controlpoints = lower
        self.apply_splines()

    def scale(self, factor: float) -> None:
        super().scale(factor)
        self.upper_spline.controlpoints = self.upper_spline.controlpoints.scale(euklid.vector.Vector2D([1, factor]))
        self.lower_spline.controlpoints = self.lower_spline.controlpoints.scale(euklid.vector.Vector2D([1, factor]))
