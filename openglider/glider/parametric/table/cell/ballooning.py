from typing import List, Tuple

from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable

import logging

logger = logging.getLogger(__name__)

class BallooningTable(ElementTable):
    keywords = [
        ("BallooningFactor", 1),
        ("BallooningMerge", 1),
    ]

    def get_merge_factors(self, factor_list) -> List[Tuple[float, float]]:

        merge_factors = factor_list[:]

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



