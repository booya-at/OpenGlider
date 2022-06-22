from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Tuple

import euklid
import openglider.jsonify
from openglider.utils.dataclass import dataclass
import openglider.vector

if TYPE_CHECKING:
    from openglider.glider.cell import Cell

logger = logging.getLogger(__name__)



@dataclass
class PanelRigidFoil:
    x_start: float
    x_end: float
    y: float = 0.5
    channel_width: float = 0.01
    
    def get_length(self, cell: Cell) -> float:
        line, start, end = self._get_flattened_line(cell)

        return line.get(start, end).get_length()
    
    def _get_flattened_line(self, cell: Cell) -> Tuple[euklid.vector.PolyLine2D, float, float]:
        flattened_cell = cell.get_flattened_cell()
        left, right = flattened_cell["ballooned"]
        line = left.mix(right, self.y)

        ik_front = (cell.rib1.profile_2d(self.x_start) + cell.rib2.profile_2d(self.x_start))/2
        ik_back = (cell.rib1.profile_2d(self.x_end) + cell.rib2.profile_2d(self.x_end))/2

        return line, ik_front, ik_back

    def draw_panel_marks(self, cell: Cell, panel):
        line, ik_front, ik_back = self._get_flattened_line(cell)

        #ik_values = panel._get_ik_values(cell, numribs=5)
        ik_interpolation_front, ik_interpolation_back = panel._get_ik_interpolation(cell, numribs=5)

        start = max(ik_front, ik_interpolation_front.get_value(self.y))
        stop = min(ik_back, ik_interpolation_back.get_value(self.y))

        if start < stop:
            return line.get(start, stop)

    def get_flattened(self, cell: Cell) -> openglider.vector.drawing.PlotPart:
        line, ik_front, ik_back = self._get_flattened_line(cell)

        left = line.offset(-self.channel_width/2)
        right = line.offset(self.channel_width/2)

        contour = left.get(ik_front, ik_back) + right.get(ik_back, ik_front)

        # todo!
        #contour.close()

        marks = []

        panel_iks = []
        for panel in cell.panels:
            interpolations = panel._get_ik_interpolation(cell, numribs=5)

            panel_iks.append(interpolations[0].get_value(self.y))
            panel_iks.append(interpolations[1].get_value(self.y))
        
        for ik in panel_iks:
            if ik_front < ik < ik_back:
                marks.append(euklid.vector.PolyLine2D([
                    left.get(ik), right.get(ik)
                ]))

        return openglider.vector.drawing.PlotPart(
            cuts=[contour],
            marks=marks
        )
