import math
from typing import List
import logging

import euklid
from openglider.glider.shape import Shape
from openglider.utils import linspace
from openglider.utils.dataclass import dataclass
from openglider.utils.table import Table


logger = logging.getLogger(__name__)


@dataclass
class ParametricShape:
    front_curve: euklid.spline.SymmetricBSplineCurve
    back_curve: euklid.spline.SymmetricBSplineCurve
    rib_distribution: euklid.spline.BSplineCurve
    cell_num: int
    stabi_cell: bool = False
    stabi_cell_width: float = 0.5
    stabi_cell_length: float = 0.8


    num_shape_interpolation = 50
    num_distribution_interpolation = 50
    num_depth_integral = 50
    baseline_pos = 0.25

    def __post_init__(self):
        self.rescale_curves()

    def __repr__(self):
        return "{}\n\tcells: {}\n\tarea: {:.2f}\n\taspect_ratio: {:.2f}".format(
            super(ParametricShape, self).__repr__(),
            self.cell_num,
            self.area,
            self.aspect_ratio
        )
    
    def copy(self):
        return self.__class__(
            self.front_curve.copy(),
            self.back_curve.copy(),
            self.rib_distribution.copy(),
            self.cell_num,
            stabi_cell=self.stabi_cell
        )

    @property
    def baseline(self) -> euklid.vector.PolyLine2D:
        return self.get_baseline(self.baseline_pos)

    def get_baseline(self, pct) -> euklid.vector.PolyLine2D:
        shape = self.get_half_shape()
        line = []
        for i in range(shape.rib_no):
            line.append(shape.get_point(i, pct))

        return euklid.vector.PolyLine2D(line)

    @property
    def has_center_cell(self) -> bool:
        return self.cell_num % 2 > 0

    @property
    def half_cell_num(self) -> int:
        return self.cell_num // 2 + self.has_center_cell + self.stabi_cell

    @property
    def half_rib_num(self) -> int:
        return self.half_cell_num + 1 - self.has_center_cell + self.stabi_cell

    def rescale_curves(self) -> None:
        span = self.span

        dist_scale = 1 / self.rib_distribution.controlpoints.nodes[-1][0]
        self.rib_distribution.controlpoints = self.rib_distribution.controlpoints.scale(
            euklid.vector.Vector2D([dist_scale, 1])
        )

        back_scale = span / self.back_curve.controlpoints.nodes[-1][0]
        self.back_curve.controlpoints = self.back_curve.controlpoints.scale(
            euklid.vector.Vector2D([back_scale, 1])
        )

    @property
    def rib_dist_interpolation(self):
        """
        Interpolate Cell-distribution
        """
        data = self.rib_distribution.get_sequence(self.num_distribution_interpolation)
        interpolation = euklid.vector.Interpolation([[p[1], p[0]] for p in data])
        start = self.has_center_cell / self.cell_num
        num = self.cell_num // 2 + 1
        return [[interpolation.get_value(i), i] for i in linspace(start, 1, num)]

    # besser mit spezieller bezier?
    @property
    def rib_dist_controlpoints(self) -> euklid.vector.PolyLine2D:
        return euklid.vector.PolyLine2D(self.rib_distribution.controlpoints.nodes[1:-1])

    @rib_dist_controlpoints.setter
    def rib_dist_controlpoints(self, arr):
        self.rib_distribution.controlpoints = [[0, 0]] + arr + [[1, 1]]

    @property
    def rib_x_values(self) -> List[float]:
        xvalues = [p[0]*self.span for p in self.rib_dist_interpolation]

        if self.stabi_cell:
            width = 0.4 * (xvalues[-1] - xvalues[-2])
            xvalues.append(xvalues[-1] + width)
        
        return xvalues


    @property
    def cell_x_values(self) -> List[float]:
        ribs = self.rib_x_values
        if self.has_center_cell:
            ribs.insert(0, -ribs[0])

        cells = []
        for x1, x2 in zip(ribs[:-1], ribs[1:]):
            cells.append((x1+x2)/2)

        return cells

    def get_half_shape(self) -> Shape:
        """
        Return shape of the glider:
        [ribs, front, back]
        """
        self.rescale_curves()
        num = self.num_shape_interpolation
        front_int = euklid.vector.Interpolation(self.front_curve.get_sequence(num).nodes)
        back_int = euklid.vector.Interpolation(self.back_curve.get_sequence(num).nodes)
        distribution = self.rib_x_values

        front = [[x, front_int.get_value(x)] for x in distribution]
        back = [[x, back_int.get_value(x)] for x in distribution]

        if self.stabi_cell:
            y1 = front[-2][1]
            y2 = back[-2][1]
            delta = (y2 - y1) * (1-self.stabi_cell_length)

            front[-1][1] = y1 + delta
            back[-1][1] = y2 - delta
        
        if self.has_center_cell:
            p1 = front[0][:]
            p1[0] = - p1[0]
            front.insert(0, p1)

            p2 = back[0][:]
            p2[0] = - p2[0]
            back.insert(0, p2)
            
        return Shape(euklid.vector.PolyLine2D(front), euklid.vector.PolyLine2D(back))

    def get_shape(self) -> Shape:
        """
        Return shape of the glider:
        [ribs, front, back]
        """
        return self.get_half_shape().copy_complete()

    def __getitem__(self, pos) -> euklid.vector.Vector2D:
        """if first argument is negative the point is returned mirrored"""
        rib_nr, rib_pos = pos
        ribs = self.ribs
        neg = (rib_nr < 0)
        sign = -neg * 2 + 1
        if rib_nr > len(ribs):
            raise ValueError(f"invalid rib_nr: {rib_nr}")

        fr, ba = ribs[abs(rib_nr + neg * self.has_center_cell)]
        chord = ba[1] - fr[1]
        x = fr[0]
        y = fr[1] + rib_pos * chord
        return euklid.vector.Vector2D([sign * x, y])

    @property
    def ribs(self):
        return self.get_half_shape().ribs

    def get_rib_point(self, rib_no, x):
        ribs = list(self.ribs)
        rib = ribs[rib_no]

        return rib[0] + (rib[1] - rib[0]) * x

    def get_shape_point(self, x, y):
        k = x%1
        rib1 = int(x)
        p1 = self.get_rib_point(rib1, y)

        if k > 0:
            p2 = self.get_rib_point(rib1+1, y)
            return p1 + (p2-p1) * k
        else:
            return p1

    @property
    def depth_integrated(self):
        """
        Return A(x)
        """
        num = self.num_depth_integral
        x_values = linspace(0, self.span, num)
        front_int = euklid.vector.Interpolation(self.front_curve.get_sequence(num).nodes)
        back_int = euklid.vector.Interpolation(self.back_curve.get_sequence(num).nodes)
        integrated_depth = [0.]
        for x in x_values[1:]:
            depth = front_int.get_value(x) - back_int.get_value(x)
            integrated_depth.append(integrated_depth[-1] + 1. / depth)
        y_values = [i / integrated_depth[-1] for i in integrated_depth]

        x_values_normalized = [x/self.span for x in x_values]
        return zip(x_values_normalized, y_values)

    def set_const_cell_dist(self) -> None:
        const_dist = list(self.depth_integrated)
        num_pts = len(self.rib_distribution.controlpoints)
        self.rib_distribution = self.rib_distribution.fit(const_dist, numpoints=num_pts)

    ############################################################################
    # scaling stuff
    def scale(self, x=1., y=None):
        if y is None:
            y = x

        print("scale factor: ", x, y)
        self.front_curve.controlpoints = self.front_curve.controlpoints.scale([x, y])

        # scale back to fit with front
        factor = self.front_curve.controlpoints.nodes[-1][0] / self.back_curve.controlpoints.nodes[-1][0]
        self.back_curve.controlpoints = self.back_curve.controlpoints.scale([factor, y])

        # scale rib_dist
        #factor = 1 / self.rib_distribution.controlpoints.nodes[-1][0]
        #self.rib_distribution.controlpoints = self.rib_distribution.controlpoints.scale([factor, 1])

    @property
    def area(self) -> float:
        return self.get_shape().area

    def set_area(self, area, fixed="aspect_ratio"):
        if fixed == "aspect_ratio":
            # scale proportional
            factor = math.sqrt(area/self.area)
            self.scale(factor, factor)
        elif fixed == "span":
            # scale y
            factor = area/self.area
            self.scale(1, factor)
        elif fixed == "depth":
            # scale span
            factor = area/self.area
            self.scale(factor, 1)
        else:
            raise ValueError("Invalid Value: {} for 'constant' (aspect_ratio, span, depth)".format(fixed))

        return self.area

    def get_sweep(self):
        ribs = self.ribs

        center_f = ribs[0][0]
        center_b = ribs[0][1]

        if self.stabi_cell:
            tip_rib = ribs[-2]
        else:
            tip_rib = ribs[-1]

        tip_f = tip_rib[0]
        tip_b = tip_rib[1]

        dy = ((tip_f + tip_b) * 0.5)[1] - center_f[1]

        return dy / (center_f + center_b)[1]
    
    def _clean(self):
        p0 = self.front_curve.get(0) * [0, -1]
        self.front_curve.controlpoints = self.front_curve.controlpoints.move(p0)
        self.back_curve.controlpoints = self.back_curve.controlpoints.move(p0)
    
    def set_sweep(self, sweep):
        current_sweep = self.get_sweep()
        self.rescale_curves()

        ribs = self.ribs
        if self.stabi_cell:
            ribs.pop(-1)

        center_chord = (ribs[0][0] - ribs[0][1]).length()
        diff = (current_sweep - sweep) * center_chord

        x0 = ribs[0][0][0]
        span = ribs[-1][0][0] - x0

        front = euklid.vector.PolyLine2D([p + [0, (p[0]-x0)*diff/span] for p, _ in ribs])
        back = euklid.vector.PolyLine2D([p + [0, (p[0]-x0)*diff/span] for _, p in ribs])

        self.front_curve = self.front_curve.fit(front, self.front_curve.numpoints)
        self.back_curve = self.back_curve.fit(back, self.back_curve.numpoints)

        y0 = self.ribs[0][0][1]

        self.front_curve.controlpoints = self.front_curve.controlpoints.move([0, -y0])
        self.back_curve.controlpoints = self.back_curve.controlpoints.move([0, -y0])
        
        return self

    @property
    def aspect_ratio(self) -> float:
        # todo: span -> half span, area -> full area???
        return (2*self.span) ** 2 / self.area

    def set_aspect_ratio(self, ar, fixed="span") -> None:
        ar0 = self.aspect_ratio
        if fixed == "span":
            self.scale(y=ar0 / ar)
        elif fixed == "area":
            self.scale(x=math.sqrt(ar / ar0), y=math.sqrt(ar0 / ar))

    @property
    def span(self) -> float:
        span = self.front_curve.controlpoints.nodes[-1][0]
        return span

    @span.setter
    def span(self, span: float):
        factor = span/self.span
        self.scale(factor, 1)

    def set_span(self, span, fixed="area") -> None:
        span_0 = self.span
        if fixed == "area":
            self.scale(x=span / span_0, y=span_0 / span)
        elif fixed == "aspect_ratio":
            self.scale(x=span/span_0, y=span/span_0)
        else:
            self.scale(x=span/span_0, y=1)
