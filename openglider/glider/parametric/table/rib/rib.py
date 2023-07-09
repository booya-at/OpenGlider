import logging
from typing import Any, Dict, List, Optional

from openglider.glider.parametric.table.base import Keyword, RibTable, dto
from openglider.glider.rib.singleskin import SingleSkinParameters
from openglider.utils.table import Table
from openglider.vector.unit import Angle, Percentage

logger = logging.getLogger(__name__)

class SkinRib(dto.DTO):
    continued_min_end: Percentage
    xrot: Angle

    def get_object(self) -> tuple[SingleSkinParameters, Angle]:
        return SingleSkinParameters(continued_min_end=self.continued_min_end), self.xrot

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
    ], target_cls=Dict[str, Any])

class SingleSkinTable(RibTable):
    keywords: Dict[str, Keyword] = {
        "SkinRib7": SkinRib7,
        "XRot": Keyword([("angle", float)], target_cls=dict)
    }
    dtos = {
        "SkinRib": SkinRib
    }

    def get_singleskin_ribs(self, rib_no: int, **kwargs: Any) -> tuple[SingleSkinParameters, Angle] | None:
        return self.get_one(rib_no, ["SkinRib"], **kwargs)
    
    def get_xrot(self, rib_no: int) -> float:
        rotation = 0
        if rot := self.get(rib_no, keywords=["XRot"]):
            if len(rot) > 1:
                logger.warning(f"multiple xrot values: {rot}; using the last one")
            rotation = rot[-1]["angle"]
        
        return rotation
