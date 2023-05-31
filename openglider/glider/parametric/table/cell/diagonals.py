from typing import Any, Dict, List

from openglider.glider.cell.diagonals import DiagonalRib, DiagonalSide, TensionLine, TensionStrap
from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.base import CellTable, Keyword
from openglider.glider.parametric.table.base.parser import Parser
from openglider.utils.table import Table

import logging

logger = logging.getLogger(__name__)

class DiagonalTable(CellTable):

    def __init__(self, table: Table=None, file_version: int=None, migrate: bool=False):
        if file_version == 1:
            pass
            # height (0,1) -> (-1,1)
            # TODO
            #height1 = height1 * 2 - 1
            #height2 = height2 * 2 - 1

        super().__init__(table, migrate_header=migrate)


    keywords = {
        "QR": Keyword(["left", "right", "width_left", "width_right", "height_left", "height_right"], target_cls=DiagonalRib)
    }
    
    def get_element(self, row: int, keyword: str, data: List[Any], resolvers: list[Parser]=None, **kwargs: Any) -> DiagonalRib:
        assert resolvers is not None
        r1 = resolvers[row]
        r2 = resolvers[row + 1]

        left = r1.parse(data[0])
        right = r2.parse(data[1])
        name = None

        if name is not None:
            name = f"D{row}{name}"
        else:
            name = f"D{row}-"

        if keyword == "QR":
            # left, right, width_left, width_right, height_left, height_right

            left_side = DiagonalSide.create_from_center(left, r1.parse(data[2]), data[4])
            right_side = DiagonalSide.create_from_center(right, r2.parse(data[3]), data[5])

            return DiagonalRib(left_side, right_side, name=name)      

        raise ValueError()


class StrapTable(CellTable):
    keywords = {
        "STRAP": Keyword([("left", float) , ("right", float), ("width", float)], target_cls=TensionStrap),  # left, right, width
        "VEKTLAENGE": Keyword(["left", "right"], target_cls=TensionLine)
    }
    
    def get_element(self, row: int, keyword: str, data: List[Any], resolvers: list[Parser]=None, **kwargs: Any) -> DiagonalRib:
        assert resolvers is not None
        r1 = resolvers[row]
        r2 = resolvers[row+1]

        data[0] = r1.parse(data[0])
        data[1] = r2.parse(data[1])
        name = None
        
        if len(data) > 2:
            return TensionStrap(
                data[0],
                data[1],
                (r1.parse(data[2]), r2.parse(data[2]))
            )

        return super().get_element(row, keyword, data, name=name)
