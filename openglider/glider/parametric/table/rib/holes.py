from openglider.glider.parametric.table.elements import ElementTable, Keyword

from openglider.glider.rib.crossports import RibHole, RibSquareHole, MultiSquareHole

import logging

logger = logging.getLogger(__name__)

class HolesTable(ElementTable):
    keywords = {
        "HOLE": Keyword(["pos", "size"], target_cls=RibHole),
        "QUERLOCH": Keyword(["pos", "size"], target_cls=RibHole),
        "HOLE5": Keyword(["pos", "size", "width", "vertical_shift", "rotation"], target_cls=RibHole),
        "HOLESQ": Keyword(["x", "width", "height"], target_cls=RibSquareHole),
        "HOLESQMULTI": Keyword(["start", "end", "height", "num_holes", "border_width"], target_cls=MultiSquareHole),
    }
