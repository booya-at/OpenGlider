from typing import Dict, Optional

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable, Keyword

import logging

logger = logging.getLogger(__name__)

SkinRib7 = Keyword([
    "att_dist",
    "height",
    "continued_min",
    "continued_min_angle",
    "continued_min_delta_y",
    "continued_min_end",
    "continued_min_x",
    "double_first",
    "le_gap",
    "straight_te",
    "te_gap",
    "num_points",
], target_cls=dict)

class SingleSkinTable(ElementTable):
    keywords = {
        "SkinRib": Keyword(["continued_min_end", "xrot"], target_cls=dict),
        "SkinRib7": SkinRib7,
        "XRot": Keyword(["angle"], target_cls=dict)
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
