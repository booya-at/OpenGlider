from typing import Tuple, List, Optional

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import CellTable, Keyword, KeywordsType
from openglider.glider.cell.panel import PanelCut

import logging

logger = logging.getLogger(__name__)

def cut_kw(extra_keywords: Optional[KeywordsType]=None):
    keywords: KeywordsType = [("x_left", float), ("x_right", float)]
    
    keywords += extra_keywords or []

    return Keyword(keywords)

class CutTable(CellTable):
    keywords = {
        "CUT_ROUND": cut_kw([("center", float), ("amount", float)]),
        "EKV": cut_kw(),
        "EKH": cut_kw(),
        "folded": cut_kw(),
        "DESIGNM": cut_kw(),
        "DESIGNO": cut_kw(),
        "orthogonal": cut_kw(),
        "CUT3D": cut_kw(),
        "cut_3d": cut_kw(),
        "singleskin": cut_kw(),
    }

    def get_element(self, row, keyword, data, curves=None):
        left, right = data[:2]
        if isinstance(left, str):
            left = curves[left].get(row)
        if isinstance(right, str):
            right = curves[right].get(row+1)
            
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
            return PanelCut(x_left=data[0], x_right=data[1], cut_type=cut_type, x_center=data[2], seam_allowance=data[3])
        else:
            raise ValueError(f"invalid keyword: {keyword}")
        
        return PanelCut(x_left=data[0], x_right=data[1], cut_type=cut_type)
