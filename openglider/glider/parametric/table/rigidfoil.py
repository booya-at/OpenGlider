from openglider.glider.parametric.table.elements import ElementTable, Keyword

from openglider.glider.cell.elements import PanelRigidFoil
from openglider.glider.rib.elements import RigidFoil

import logging

logger = logging.getLogger(__name__)

class RibRigidTable(ElementTable):
    keywords = {
        "RIGIDFOIL": Keyword(["start", "end", "distance"], target_cls=RigidFoil)
    }


class CellRigidTable(ElementTable):
    keywords = {
        "RIGIDFOIL": Keyword(["x_start", "x_end", "y"], target_cls=PanelRigidFoil)
    }
