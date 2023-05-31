from openglider.glider.parametric.table.base import CellTable, RibTable, Keyword

from openglider.glider.cell.rigidfoil import PanelRigidFoil
from openglider.glider.rib.rigidfoils import RigidFoil, RigidFoil2

import logging

logger = logging.getLogger(__name__)

class RibRigidTable(RibTable):
    keywords = {
        "RIGIDFOIL": Keyword(["start", "end", "distance"], target_cls=RigidFoil),
        "RIGIDFOIL3": Keyword(["start", "end", "distance"], target_cls=RigidFoil2),
        "RIGIDFOIL5": Keyword(["start", "end", "distance", "circle_radius", "circle_amount"], target_cls=RigidFoil2)
    }


class CellRigidTable(CellTable):
    keywords = {
        "RIGIDFOIL": Keyword(["x_start", "x_end", "y"], target_cls=PanelRigidFoil)
    }
