from typing import Callable, Optional
import euklid

from openglider.airfoil import Profile3D
from openglider.utils.dataclass import dataclass, field



@dataclass
class MiniRib:
    yvalue: float
    front_cut: float
    back_cut: float=1.
    name: str="unnamed_minirib"

    function: euklid.vector.Interpolation = field(default_factory=lambda: euklid.vector.Interpolation([]))

    def __post_init__(self):
        p1_x = 2/3

        if len(self.function.nodes) == 0:
            if front_cut > 0:
                points = [[front_cut, 1], [front_cut + (back_cut - front_cut) * (1-p1_x), 0]]  #
            else:
                points = [[0, 0]]

            if back_cut < 1:
                points = points + [[front_cut + (back_cut-front_cut) * p1_x, 0], [back_cut, 1]]
            else:
                points = points + [[1., 0.]]

            curve = euklid.spline.BSplineCurve(points).get_sequence(100)
            self.function = euklid.vector.Interpolation(curve.nodes)

    def multiplier(self, x: float):
        if self.front_cut <= abs(x) <= self.back_cut:
            return min(1, max(0, self.function.get_value(abs(x))))
        else:
            return 1

    def get_3d(self, cell):
        shape_with_bal = cell.basic_cell.midrib(self.y_value,
                                                       True).data
        shape_wo_bal = cell.basic_cell.midrib(self.y_value,
                                                          False).data

        points = []
        for xval, with_bal, without_bal in zip(
                cell.x_values, shape_with_bal, shape_wo_bal):
            fakt = self.multiplier(xval)  # factor ballooned/unb. (0-1)
            point = without_bal + fakt * (with_bal - without_bal)
            points.append(point)

        return Profile3D(points)

    def get_flattened(self, cell):
        prof_3d = self.get_3d(cell)
        prof_flat = prof_3d.flatten()
        prof_normalized = prof_flat.copy().normalized()

        p1 = prof_normalized(-self.back_cut)
        p2 = prof_normalized(-self.front_cut)

        p3 = prof_normalized(self.front_cut)
        p4 = prof_normalized(self.back_cut)

        raise NotImplementedError()

