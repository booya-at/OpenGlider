from typing import Any, Dict, List
from openglider.glider import curve
from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.elements import RibTable, Keyword

from openglider.glider.rib.crossports import RibHole, RibSquareHole, MultiSquareHole, AttachmentPointHole

import logging

logger = logging.getLogger(__name__)

class HolesTable(RibTable):
    keywords = {
        "HOLE": Keyword(["pos", "size"], target_cls=RibHole),
        "QUERLOCH": Keyword(["pos", "size"], target_cls=RibHole),
        "HOLE5": Keyword(["pos", "size", "width", "vertical_shift", "rotation"], target_cls=RibHole),
        "HOLESQ": Keyword(["x", "width", "height"], target_cls=RibSquareHole),
        "HOLESQMULTI": Keyword(["start", "end", "height", "num_holes", "border_width"], target_cls=MultiSquareHole),
        "HOLESQMULTI6": Keyword(["start", "end", "height", "num_holes", "border_width", "margin"], target_cls=MultiSquareHole),
        "HOLEATP": Keyword(["start", "end", "height", "num_holes"], target_cls=AttachmentPointHole),
        "HOLEATP6": Keyword(["start", "end", "height", "num_holes", "border", "side_border"], target_cls=AttachmentPointHole),
        "HOLEATP7": Keyword(["start", "end", "height", "num_holes", "border", "side_border", "corner_size"], target_cls=AttachmentPointHole)
    }


    def get_element(self, row: int, keyword: str, data: List[Any], curves: Dict[str, GliderCurveType]=None, **kwargs: Any) -> Any:
        if curves is None:
            raise ValueError("No curves specified")

        for i, value in enumerate(data):
            if isinstance(value, str):
                data[i] = curves[value].get(row)

        return super().get_element(row, keyword, data)
