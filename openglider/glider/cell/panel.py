import euklid

import openglider
from openglider.utils.cache import cached_function
from openglider.airfoil import get_x_value

class StraightCut:
    def __init__(self, x_left, x_right):
        self.x_left = x_left
        self.x_right = x_right

    @cached_function("self")
    def _get_ik_values(self, cell: "openglider.glider.cell.Cell", numribs=0, exact=True):
        """
        :param cell: the parent cell of the panel
        :param numribs: number of interpolation steps between ribs
        :return: [[front_ik_0, back_ik_0], ..[front_ik_n, back_ik_n]] with n is numribs + 1
        """
        # TODO: move to cut!!
        x_values_left = cell.rib1.profile_2d.x_values
        x_values_right = cell.rib2.profile_2d.x_values

        ik_left = get_x_value(x_values_left, self.x_left)
        ik_right = get_x_value(x_values_right, self.x_right)

        ik_values = [ik_left]

        for i in range(numribs):
            y = float(i+1)/(numribs+1)

            ik = ik_left + y * (ik_right - ik_left)
            ik_values.append(ik)
        
        ik_values.append(ik_right)

        if not exact:
            return ik_values

        ik_values_new = []
        inner = cell.get_flattened_cell(num_inner=numribs+2)["inner"]
        p_front_left = inner[0].get(ik_left)
        p_front_right = inner[-1].get(ik_right)

        for i, ik in enumerate(ik_values):
            ik_front = ik
            line: euklid.vector.PolyLine2D = inner[i]

            _ik_front, _ = line.cut(p_front_left, p_front_right, ik_front)

            if abs(_ik_front-ik_front) > 20:
                _ik_front = ik_front

            ik_values_new.append(_ik_front)
        
        return ik_values_new
    
    def get_curve_3d(self, cell: "openglider.glider.cell.Cell", numribs=0, exact=True):
        ik_values = self._get_ik_values(cell, numribs, exact)

        ribs = cell.get_midribs(numribs+2)
        points = [rib.get(ik) for rib, ik in zip(ribs, ik_values)]

        return euklid.vector.PolyLine3D(points)
