from openglider.glider.parametric.table.base import CellTable, RibTable, Keyword

from openglider.glider.cell.rigidfoil import PanelRigidFoil
from openglider.glider.rib.rigidfoils import RigidFoil, RigidFoil2
from openglider.glider.parametric.table.base.dto import DTO
import logging

from openglider.vector.unit import Length, Percentage

logger = logging.getLogger(__name__)

class RigidFoilDTO(DTO[RigidFoil]):
    start: Percentage
    end: Percentage
    distance: Length
    
    def get_object(self) -> RigidFoil:
        return RigidFoil(**self.dict())
    
class RigidFoil3(DTO[RigidFoil2]):
    start: Percentage
    end: Percentage
    distance: Length
    def get_object(self) -> RigidFoil2:
        return RigidFoil2(**self.dict())

class RigidFoil5(RigidFoil3):
    circle_radius: Length
    circle_amount: Percentage

class RibRigidTable(RibTable):
    dtos = {
        "RIGIDFOIL": RigidFoilDTO,
        "RIGIDFOIL3": RigidFoil3,
        "RIGIDFOIL5": RigidFoil5
    }


class CellRigidTable(CellTable):
    keywords = {
        "RIGIDFOIL": Keyword(["x_start", "x_end", "y"], target_cls=PanelRigidFoil)
    }
