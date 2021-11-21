from typing import List, Tuple, Optional
import logging

from pyfoil import Airfoil

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable, Keyword

logger = logging.getLogger(__name__)

class ProfileTable(ElementTable):
    keywords = {
        "ProfileFactor": Keyword(attributes=["thickness_factor"]),
        "ProfileMerge": Keyword(attributes=["merge_factor"]),
        "Flap": Keyword(attributes=["begin", "amount"])
    }

    def get_element(self, row, keyword, data):
        return data

    def get_merge_factors(self, merge_factor_list: List[float]) -> List[Tuple[float, float]]:

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
    
    def get_flap(self, row_no: int) -> Optional[Tuple[float, float]]:
        flaps = self.get(row_no, keywords=["Flap"])
        flap = None

        if len(flaps) > 1:
            raise ValueError(f"Multiple Flaps defined for row {row_no}")
        elif len(flaps) == 1:
            flap = flaps[0]
            return flap
        
        return None
    
    def get_factors(self, row_no: int) -> Tuple[Optional[float], Optional[float]]:
        merge_factors = self.get(row_no, keywords=["ProfileMerge"])
        scale_factors = self.get(row_no, keywords=["ProfileFactor"])

        merge = None
        scale = None

        if len(merge_factors):
            merge = merge_factors[-1]
        
        if len(scale_factors):
            scale = scale_factors[-1]

        return merge, scale

        





