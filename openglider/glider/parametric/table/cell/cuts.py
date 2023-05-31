from typing import Any, Dict, Tuple, List, Optional
from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.base.parser import Parser

from openglider.utils.table import Table
from openglider.glider.parametric.table.base import CellTable, Keyword, KeywordsType
from openglider.glider.cell.panel import PanelCut, PANELCUT_TYPES

import logging

logger = logging.getLogger(__name__)

def cut_kw(extra_keywords: Optional[KeywordsType]=None) -> Keyword:
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

    def get_element(self, row: int, keyword: str, data: List[Any], resolvers: list[Parser]=None, **kwargs: Any) -> PanelCut:            
        assert resolvers is not None

        left = resolvers[row].parse(data[0])
        right = resolvers[row+1].parse(data[1])

        cut_type = None
        if keyword in ("EKV", "EKH", "folded"):
            cut_type = PANELCUT_TYPES.folded
        elif keyword in ("DESIGNM", "DESIGNO", "orthogonal"):
            cut_type = PANELCUT_TYPES.orthogonal
        elif keyword in ("CUT3D", "cut_3d"):
            cut_type = PANELCUT_TYPES.cut_3d
        elif keyword == "singleskin":
            cut_type = PANELCUT_TYPES.singleskin
        elif keyword == "CUT_ROUND":
            cut_type = PANELCUT_TYPES.round
            return PanelCut(x_left=left, x_right=right, cut_type=cut_type, x_center=data[2], seam_allowance=data[3])
        else:
            raise ValueError(f"invalid keyword: {keyword}")
        
        return PanelCut(x_left=left, x_right=right, cut_type=cut_type)
