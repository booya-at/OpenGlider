from typing import Dict, List, Tuple

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import CellTable, Keyword

import logging

logger = logging.getLogger(__name__)

class BallooningTable(CellTable):
    keywords: Dict[str, Keyword] = {
        "BallooningFactor": Keyword(attributes=["amount_factor"]),
        "BallooningMerge": Keyword(attributes=["merge_factor"]),
    }

    def get_merge_factors(self, factor_list: List[float]) -> List[Tuple[float, float]]:

        merge_factors = factor_list[:]

        columns = self.get_columns(self.table, "BallooningMerge", 1)
        if len(columns):
            for i in range(len(merge_factors)):
                for column in columns:
                    value = column[i+2, 0]
                    if value is not None:
                        merge_factors[i] = value

        multipliers = [1] * len(merge_factors)
        columns = self.get_columns(self.table, "BallooningFactor", 1)

        for i in range(len(merge_factors)):
            for column in columns:
                value = column[i+2, 0]
                if value is not None:
                    multipliers[i] = value
        
        return list(zip(merge_factors, multipliers))




