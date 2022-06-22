from typing import Dict, Optional

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import RibTable, Keyword

import logging

logger = logging.getLogger(__name__)

SkinRib7 = Keyword([
    ("att_dist", float),
    ("height", float),
    ("continued_min", bool),
    ("continued_min_angle", float),
    ("continued_min_delta_y", float),
    ("continued_min_end", float),
    ("continued_min_x", float),
    ("double_first", bool),
    ("le_gap", bool),
    ("straight_te", bool),
    ("te_gap", bool),
    ("num_points", int)
    ], target_cls=dict)

class SingleSkinTable(RibTable):
    keywords = {
        "SkinRib": Keyword([("continued_min_end", float), ("xrot", float)], target_cls=dict),
        "SkinRib7": SkinRib7,
        "XRot": Keyword([("angle", float)], target_cls=dict)
    }

    def get_singleskin_ribs(self, rib_no: int):
        return self.get(rib_no, keywords=["SkinRib", "SkinRib7"])
    
    def get_xrot(self, rib_no: int) -> float:
        rotation = 0
        if rot := self.get(rib_no, keywords=["XRot"]):
            if len(rot) > 1:
                logger.warning(f"multiple xrot values: {rot}; using the last one")
            rotation = rot[-1]["angle"]
        
        return rotation
