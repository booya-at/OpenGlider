from openglider.glider.parametric.table.elements import ElementTable

from openglider.glider.cell.elements import PanelRigidFoil
from openglider.glider.rib.elements import RigidFoil

import logging

logger = logging.getLogger(__name__)

class RibRigidTable(ElementTable):
    keywords = [
        ("RIGIDFOIL", 3) # start, end, distance
    ]
    
    def get_element(self, row, keyword, data):
        return RigidFoil(data[0], data[1], data[2])


class CellRigidTable(ElementTable):
    keywords = [
        ("RIGIDFOIL", 3) # x_start, x_end, y
    ]
    
    def get_element(self, row, keyword, data):
        return PanelRigidFoil(data[0], data[1], data[2])