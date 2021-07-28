from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable
from openglider.glider.cell.panel import PanelCut

import logging

logger = logging.getLogger(__name__)

class CutTable(ElementTable):
    _old_names = ("EKV", "EKH", "folded", "DESIGNM", "DESIGNO", "orthogonal", "CUT3D", "cut_3d", "singleskin")
    
    keywords = [] + [
        (name, 2) for name in _old_names
    ]
    
    def get_element(self, keyword, data):
        cut_type = None
        if keyword in ("EKV", "EKH", "folded"):
            cut_type = PanelCut.CUT_TYPES.folded
        elif keyword in ("DESIGNM", "DESIGNO", "orthogonal"):
            cut_type = PanelCut.CUT_TYPES.orthogonal
        elif keyword in ("CUT3D", "cut_3d"):
            cut_type = PanelCut.CUT_TYPES.cut_3d
        elif keyword == "singleskin":
            cut_type = PanelCut.CUT_TYPES.singleskin
        else:
            raise ValueError(f"invalid keyword: {keyword}")
        
        return PanelCut(data[0], data[1], cut_type)
