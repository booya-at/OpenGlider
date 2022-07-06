import copy
import math
from typing import List

import euklid
import numpy as np
from openglider.vector.polygon import CirclePart


class ArcCurve(object):
    """
    _
    """
    num_interpolation_points = 100

    def __init__(self, curve: euklid.spline.SymmetricBSplineCurve):
        self.curve = curve

    def __json__(self):
        return {"curve": self.curve}

    def copy(self) -> "ArcCurve":
        return copy.deepcopy(self)

    @staticmethod
    def has_center_cell(x_values) -> bool:
        return x_values[0] != 0

    def get_arc_positions(self, x_values) -> euklid.vector.PolyLine2D:
        """
        calculate y/z positions vor the arc-curve, given a shape's rib-x-values

        :param x_values:
        :return: [p0, p1,...]
        """
        # Symmetric-Bezier-> start from 0.5
        positions = []

        x_values = [abs(x) for x in x_values]

        arc_curve = self.curve.get_sequence(self.num_interpolation_points)
        arc_curve_length = arc_curve.get_length()
        scale_factor = arc_curve_length / x_values[-1]
        _positions = [arc_curve.walk(0, x * scale_factor) for x in x_values]
        positions = [arc_curve.get(p) for p in _positions]

        if not self.has_center_cell(x_values):
            scale_center = euklid.vector.Vector2D([0, 1])
        else:
            scale_center = euklid.vector.Vector2D([-1, 1])
        
        positions[0] = positions[0] * scale_center
        
        return euklid.vector.PolyLine2D(positions)

    def get_cell_angles(self, x_values, rad=True) -> List[float]:
        """
        Calculate cell rotation angles given a shape's rib-x-values
        :param x_values:
        :return: [rib_angles]
        """
        arc_positions = self.get_arc_positions(x_values)
        arc_positions_lst = list(arc_positions)
        cell_angles = []


        for l, r in zip(arc_positions_lst[:-1], arc_positions_lst[1:]):
            d = r - l
            angle = np.arctan2(-d[1], d[0])
            if rad:
                cell_angles.append(angle)
            else:
                cell_angles.append(angle * 180 / np.pi)

        if self.has_center_cell(x_values):
            # center cell is always straight
            cell_angles[0] = 0.

        return cell_angles

    @classmethod
    def from_cell_angles(cls, angles: List[float], x_values: List[float], rad=True) -> "ArcCurve":
        last_pos = euklid.vector.Vector2D([0,0])
        last_x = 0.
        nodes = []
        for i, x in enumerate(x_values):
            angle = angles[i]
            l = x - last_x
            d = euklid.vector.Vector2D([math.cos(angle), -math.sin(angle)])
            last_pos = last_pos + d * l
            last_x = x

            nodes.append(last_pos)
        
        right_curve = euklid.vector.PolyLine2D(nodes)
        left_curve = right_curve.mirror()

        curve = euklid.vector.PolyLine2D(left_curve.nodes[:-1] + right_curve.nodes)
        
        spline = euklid.spline.SymmetricBSplineCurve.fit(curve, 8) # type: ignore
        
        return cls(spline)

    def get_rib_angles(self, x_values) -> List[float]:
        """
        Calculate rib rotation angles given a shape's rib-x-values
        :param x_values:
        :return: [cell_angles]
        """
        cell_angles = self.get_cell_angles(x_values)
        rib_angles = []

        for cell_left, cell_right in zip(cell_angles[:-1], cell_angles[1:]):
            # rotation of the rib is the median of the left and right cell's rotation
            rib_angles.append((cell_left + cell_right)/2)

        # stabi rib -> same rotation as the last cell
        rib_angles.append(cell_angles[-1])

        if not self.has_center_cell(x_values):
            # center rib -> straight
            rib_angles.insert(0, 0.)
        else:
            rib_angles.insert(0, -rib_angles[0])

        return rib_angles

    def get_flattening(self, x_values) -> float:
        arc_curve = self.get_arc_positions(x_values)
        span_projected = arc_curve.nodes[-1][0]
        return span_projected / arc_curve.get_length()

    def get_circle(self, n=50) -> euklid.vector.PolyLine2D:
        p1, p2 = self.curve.get_sequence(1)
        p3 = p1 * euklid.vector.Vector2D([-1, 1])
        return CirclePart(p1, p2, p3).get_sequence(n)


    def rescale(self, x_values) -> None:
        positions = self.get_arc_positions(x_values)
        diff = euklid.vector.Vector2D([0, -positions.nodes[0][1]])
        self.curve.controlpoints = euklid.vector.PolyLine2D([p + diff for p in self.curve.controlpoints.nodes])

        arc_curve: euklid.vector.PolyLine2D = self.curve.get_sequence(self.num_interpolation_points)
        arc_curve_length = arc_curve.get_length()
        scale_factor = x_values[-1] / arc_curve_length

        self.curve.controlpoints = euklid.vector.PolyLine2D([p * scale_factor for p in self.curve.controlpoints.nodes])
