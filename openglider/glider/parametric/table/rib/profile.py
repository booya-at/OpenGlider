from typing import Any, List, Tuple, Optional, Dict
import logging
from openglider.glider.parametric.table.base.dto import DTO

from openglider.glider.rib.sharknose import Sharknose
from openglider.glider.parametric.table.base import RibTable, Keyword
from openglider.vector.unit import Angle, Length, Percentage

logger = logging.getLogger(__name__)

class FloatDict(dict):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__({
            name: float(value) for name, value in kwargs.items()
        })

class SharknoseDTO(DTO):
    position: Percentage
    amount: Percentage
    start: Percentage
    end: Percentage

    def get_object(self) -> Sharknose:
        return Sharknose(
            **self.dict()
        )

class Sharknose8(SharknoseDTO):
    angle_front: Angle
    angle_back: Angle
    rigidfoil_circle_radius: Length
    rigidfoil_circle_amount: Length

class ProfileTable(RibTable):
    keywords = {
        "ProfileFactor": Keyword(attributes=["thickness_factor"], target_cls=FloatDict),
        "ProfileMerge": Keyword(attributes=["merge_factor"], target_cls=FloatDict),
        "Flap": Keyword(attributes=["begin", "amount"], target_cls=FloatDict),
    }

    dtos = {
        "Sharknose": SharknoseDTO,
        "Sharknose8": Sharknose8,
    }

    def get_merge_factors(self, merge_factor_list: list[float]) -> list[tuple[float, float]]:
        # TODO: unused!
        merge_factors = merge_factor_list[:]

        columns = self.get_columns(self.table, "BallooningMerge", 1)
        if len(columns):
            for i in range(len(merge_factors)):
                for column in columns:
                    value = column[i+1, 0]
                    if value is not None:
                        merge_factors[i] = value

        multipliers = [1] * len(merge_factors)
        columns = self.get_columns(self.table, "BallooningFactor", 1)

        for i in range(len(merge_factors)):
            for column in columns:
                value = column[i+1, 0]
                if value is not None:
                    multipliers[i] = value
        
        return list(zip(merge_factors, multipliers))
    
    def get_sharknose(self, row_no: int, **kwargs: Any) -> Sharknose | None:
        return self.get_one(row_no, keywords=["Sharknose", "Sharknose8"], **kwargs)

    
    def get_flap(self, row_no: int) -> dict[str, float] | None:
        flaps = self.get(row_no, keywords=["Flap"])
        flap = None

        if len(flaps) > 1:
            raise ValueError(f"Multiple Flaps defined for row {row_no}")
        elif len(flaps) == 1:
            flap = flaps[0]
            return flap
        
        return None
    
    def get_factors(self, row_no: int) -> tuple[float | None, float | None]:
        merge_factors = self.get(row_no, keywords=["ProfileMerge"])
        scale_factors = self.get(row_no, keywords=["ProfileFactor"])

        merge = None
        scale = None

        if len(merge_factors):
            merge = merge_factors[-1]
        
        if len(scale_factors):
            scale = scale_factors[-1]["thickness_factor"]

        return merge, scale

        





