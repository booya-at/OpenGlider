from __future__ import annotations

from typing import TYPE_CHECKING
import euklid

from openglider.airfoil import Profile3D
from openglider.utils.dataclass import dataclass, Field

if TYPE_CHECKING:
    from openglider.glider.cell import Cell

@dataclass
class MiniRib:
    yvalue: float
    front_cut: float
    back_cut: float | None=None
    name: str="unnamed_minirib"

    function: euklid.vector.Interpolation = Field(default_factory=lambda: euklid.vector.Interpolation([]))

    class Config:
        arbitrary_types_allowed = True

    def __post_init__(self) -> None:
        p1_x = 2/3

        if self.function is None or len(self.function.nodes) == 0:
            if self.front_cut > 0:
                if self.back_cut is None:
                    back_cut = 1.
                else:
                    back_cut = self.back_cut
                points = [[self.front_cut, 1], [self.front_cut + (back_cut - self.front_cut) * (1-p1_x), 0]]  #
            else:
                points = [[0, 0]]

            if self.back_cut is not None and self.back_cut < 1.:
                points = points + [[self.front_cut + (self.back_cut-self.front_cut) * p1_x, 0], [self.back_cut, 1]]
            else:
                points = points + [[1., 0.]]

            curve = euklid.spline.BSplineCurve(points).get_sequence(100)
            self.function = euklid.vector.Interpolation(curve.nodes)

    def multiplier(self, x: float) -> float:
        within_back_cut = self.back_cut is None or abs(x) <= self.back_cut
        if self.front_cut <= abs(x) and within_back_cut:
            return min(1, max(0, self.function.get_value(abs(x))))
        else:
            return 1.

    def get_3d(self, cell: Cell) -> Profile3D:
        shape_with_bal = cell.basic_cell.midrib(self.yvalue, True).curve.nodes
        shape_wo_bal = cell.basic_cell.midrib(self.yvalue, False).curve.nodes

        points: list[euklid.vector.Vector3D] = []
        for xval, with_bal, without_bal in zip(
                cell.x_values, shape_with_bal, shape_wo_bal):
            fakt = self.multiplier(xval)  # factor ballooned/unb. (0-1)
            point = without_bal + (with_bal - without_bal) * fakt
            points.append(point)

        return Profile3D(euklid.vector.PolyLine3D(points))

    def get_flattened(self, cell: Cell) -> None:



        raise NotImplementedError()

