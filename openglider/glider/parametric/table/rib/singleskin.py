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
        "SkinRib7": SkinRib7
    }
