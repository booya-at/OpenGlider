from typing import Tuple, List
from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable
from openglider.glider.cell.panel import PanelCut

import logging

logger = logging.getLogger(__name__)

class CutTable(ElementTable):    
    keywords: List[Tuple[str, int]] = [
        ("CUT_ROUND", 4), # left, right, center, amount
        ("EKV", 2),
        ("EKH", 2),
        ("folded", 2),
        ("DESIGNM", 2),
        ("DESIGNO", 2),
        ("orthogonal", 2),
        ("CUT3D", 2),
        ("cut_3d", 2),
        ("singleskin", 2),
    ]

    def get_element(self, row, keyword, data):
        cut_type = None
        if keyword in ("EKV", "EKH", "folded"):
            cut_type = PanelCut.CUT_TYPES.folded
        elif keyword in ("DESIGNM", "DESIGNO", "orthogonal"):
            cut_type = PanelCut.CUT_TYPES.orthogonal
        elif keyword in ("CUT3D", "cut_3d"):
            cut_type = PanelCut.CUT_TYPES.cut_3d
        elif keyword == "singleskin":
            cut_type = PanelCut.CUT_TYPES.singleskin
        elif keyword == "CUT_ROUND":
            cut_type = PanelCut.CUT_TYPES.round
            return PanelCut(data[0], data[1], cut_type, x_center=data[2], seam_allowance=data[3])
        else:
            raise ValueError(f"invalid keyword: {keyword}")
        
        return PanelCut(data[0], data[1], cut_type)
