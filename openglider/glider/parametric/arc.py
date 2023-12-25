import copy
import numpy as np

from openglider.vector import PolyLine2D
from openglider.vector.spline import SymmetricBezier, SymmetricBSpline


class ArcCurve(object):
    """
    _
    """

    num_interpolation_points = 100

    def __init__(self, curve):
        self.curve = curve

    def __json__(self):
        return {"curve": self.curve}

    def copy(self):
        return copy.deepcopy(self)

    @staticmethod
    def has_center_cell(x_values):
        return x_values[0] != 0

    def get_arc_positions(self, x_values):
        """
        calculate y/z positions vor the arc-curve, given a shape's rib-x-values

        :param x_values:
        :return: [p0, p1,...]
        """
        # Symmetric-Bezier-> start from 0.5
        arc_curve = PolyLine2D(
            [self.curve(i) for i in np.linspace(0.5, 1, self.num_interpolation_points)]
        )
        arc_curve_length = arc_curve.get_length()
        scale_factor = arc_curve_length / x_values[-1]
        _positions = [arc_curve.walk(0, x * scale_factor) for x in x_values]
        positions = PolyLine2D([arc_curve[p] for p in _positions])
        if not self.has_center_cell(x_values):
            positions[0][0] = 0
        # rescale
        return positions

    def get_cell_angles(self, x_values, rad=True):
        """
        Calculate cell rotation angles given a shape's rib-x-values
        :param x_values:
        :return: [rib_angles]
        """
        arc_positions = self.get_arc_positions(x_values)
        arc_positions_lst = list(arc_positions)
        cell_angles = []

        if self.has_center_cell(x_values):
            # center cell is always straight
            cell_angles.append(0)

        for l, r in zip(arc_positions_lst[:-1], arc_positions_lst[1:]):
            d = r - l
            angle = np.arctan2(-d[1], d[0])
            if rad:
                cell_angles.append(angle)
            else:
                cell_angles.append(angle * 180 / np.pi)

        return cell_angles

    @classmethod
    def from_cell_angles(cls, angles, x_values, rad=True):
        last_pos = np.array([0, 0])
        last_x = 0
        curve = []
        for i, x in enumerate(x_values):
            angle = angles[i]
            l = x - last_x
            d = np.array([np.cos(angle), -np.sin(angle)])
            last_pos = last_pos + d * l
            last_x = x

            curve.append(last_pos)

        curve = [p * [-1, 1] for p in curve[::-1]] + curve
        spline = SymmetricBSpline.fit(curve, numpoints=8)
        return cls(spline)

    def get_rib_angles(self, x_values):
        """
        Calculate rib rotation angles given a shape's rib-x-values
        :param x_values:
        :return: [cell_angles]
        """
        cell_angles = self.get_cell_angles(x_values)
        rib_angles = []

        if not self.has_center_cell(x_values):
            # center rib -> straight
            rib_angles.append(0)

        for cell_left, cell_right in zip(cell_angles[:-1], cell_angles[1:]):
            # rotation of the rib is the median of the left and right cell's rotation
            rib_angles.append((cell_left + cell_right) / 2)

        # stabi rib -> same rotation as the last cell
        rib_angles.append(cell_angles[-1])

        return rib_angles

    def get_flattening(self, x_values):
        arc_curve = self.get_arc_positions(x_values)
        span_projected = arc_curve.last()[0]
        return span_projected / arc_curve.get_length()

    def get_circle(self):
        p1, p2 = self.curve.get_sequence(2)

    def rescale(self, x_values):
        positions = self.get_arc_positions(x_values)
        diff = [0, -positions[0][1]]
        self.curve.controlpoints = [p + diff for p in self.curve.controlpoints]

        arc_curve = PolyLine2D(
            [self.curve(i) for i in np.linspace(0.5, 1, self.num_interpolation_points)]
        )
        arc_curve_length = arc_curve.get_length()
        scale_factor = x_values[-1] / arc_curve_length

        self.curve.controlpoints = [p * scale_factor for p in self.curve.controlpoints]
