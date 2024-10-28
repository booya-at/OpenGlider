import logging
from typing import Any


from openglider.glider.parametric.table.base import Keyword, RibTable, dto
from openglider.glider.rib.singleskin import SingleSkinParameters
from openglider.vector.unit import Angle, Length, Percentage

logger = logging.getLogger(__name__)

class TrailingEdgeCut(dto.DTO):
    length: Length | Percentage

    def get_object(self) -> Length | Percentage:
        return self.length * -1
    

class RibOffset(dto.DTO):
    x: Length | Percentage
    y: Length | Percentage
    z: Length | Percentage

    def get_object(self) -> list:
        return [self.x, self.y, self.z]

class RibRotation(dto.DTO):
    x: Angle | None
    y: Angle | None
    z: Angle | None

class SkinRib(dto.DTO):
    continued_min_end: Percentage
    xrot: Angle

    def get_object(self) -> tuple[SingleSkinParameters, Angle]:
        return SingleSkinParameters(continued_min_end=self.continued_min_end), self.xrot

class SkinRib3(SkinRib):
    height: Percentage

    def get_object(self) -> tuple[SingleSkinParameters, Angle]:
        return SingleSkinParameters(
            continued_min_end=self.continued_min_end,
            height=self.height
        ), self.xrot

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
    ], target_cls=dict[str, Any])

class SingleSkinTable(RibTable):
    keywords: dict[str, Keyword] = {
        "SkinRib7": SkinRib7,
        "XRot": Keyword([("angle", float)], target_cls=dict)
    }
    dtos = {
        "SkinRib": SkinRib,
        "SkinRib3": SkinRib3,
        "TrailingEdgeCut": TrailingEdgeCut,
        "RibOffset": RibOffset,
        "RibRotation": RibRotation
    }
    
    def get_rib_args(self, rib_no: int, **kwargs: Any) -> dict[str, Any]:
        result = {}
        cut: TrailingEdgeCut | None = self.get_one(rib_no, ["TrailingEdgeCut"], **kwargs)
        if cut is not None:
            result["trailing_edge_extra"] = cut
        
        return result

    def get_singleskin_ribs(self, rib_no: int, **kwargs: Any) -> tuple[SingleSkinParameters, Angle] | None:
        return self.get_one(rib_no, ["SkinRib", "SkinRib3"], **kwargs)
    
    def get_xrot(self, rib_no: int) -> float:
        rotation = 0
        if rot := self.get(rib_no, keywords=["XRot"]):
            if len(rot) > 1:
                logger.warning(f"multiple xrot values: {rot}; using the last one")
            rotation = rot[-1]["angle"]
        
        return rotation
    
    def get_offset(self, rib_no: int, **kwargs: Any) -> list[Length | Percentage]:
        result = [0,0,0]
        offset: RibOffset | None = self.get_one(rib_no, ["RibOffset"], **kwargs)

        if offset is not None:
            result = offset
        
        return result
    
    def get_rotation(self, rib_no: int, **kwargs: Any) -> RibRotation:
        result: RibRotation | None = self.get_one(rib_no, ["RibOffset"], **kwargs)
        if result is None:
            result = RibRotation(x=None, y=None, z=None)

        return result
