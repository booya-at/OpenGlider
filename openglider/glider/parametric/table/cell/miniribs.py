from typing import Any, List
from openglider.glider.parametric.table.base.dto import DTO
from openglider.glider.rib import MiniRib

from openglider.glider.parametric.table.base import CellTable, Keyword
from openglider.vector.unit import Percentage

class MiniRibDTO(DTO):
    y_value: Percentage
    front_cut: Percentage

    def get_object(self) -> Any:
        return MiniRib(yvalue=float(self.y_value), front_cut=float(self.front_cut))

class MiniRibTable(CellTable):
    dtos = {
        "MINIRIB": MiniRibDTO
    }