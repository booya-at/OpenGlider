from typing import Any
from openglider.glider.parametric.table.base.dto import DTO
from openglider.glider.rib import MiniRib

from openglider.glider.parametric.table.base import CellTable
from openglider.vector.unit import Percentage

class MiniRibDTO(DTO):
    y_value: Percentage
    front_cut: Percentage
    material_code: str

    def get_object(self) -> Any:
        return MiniRib(yvalue=self.y_value.si, front_cut=self.front_cut.si, material_code=self.material_code)

class MiniRibTable(CellTable):
    dtos = {
        "MINIRIB": MiniRibDTO
    }