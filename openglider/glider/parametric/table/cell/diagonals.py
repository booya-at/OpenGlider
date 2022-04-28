from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import CellTable, Keyword
from openglider.glider.cell.diagonals import DiagonalRib, DiagonalSide, TensionLine, TensionStrap

import logging

logger = logging.getLogger(__name__)

class DiagonalTable(CellTable):

    def __init__(self, table: Table=None, file_version: int=None):
        if file_version == 1:
            pass
            # height (0,1) -> (-1,1)
            # TODO
            #height1 = height1 * 2 - 1
            #height2 = height2 * 2 - 1

        super().__init__(table)


    keywords = {
        "QR": Keyword(["left", "right", "width_left", "width_right", "height_left", "height_right"])
    }
    
    def get_element(self, row, keyword, data, curves):
        left = data[0]
        right = data[1]
        name = None

        if isinstance(left, str):
            name = left
            left = curves[left].get(row)

        if isinstance(right, str):
            name = right
            right = curves[right].get(row+1)

        if name is not None:
            name = f"D{row}{name}"
        else:
            name = f"D{row}-"

        if keyword == "QR":
            # left, right, width_left, width_right, height_left, height_right

            left_side = DiagonalSide.create_from_center(left, data[2], data[4])
            right_side = DiagonalSide.create_from_center(right, data[3], data[5])

            return DiagonalRib(left_side, right_side, name=name)      

        raise ValueError()


class StrapTable(CellTable):
    keywords = {
        "STRAP": Keyword(["left", "right", "width"], target_cls=TensionStrap),  # left, right, width
        "VEKTLAENGE": Keyword(["left", "right"], target_cls=TensionLine)
    }
    
    def get_element(self, row, keyword, data, curves):
        left = data[0]
        right = data[1]
        name = None

        if isinstance(left, str):
            name = left
            left = curves[left].get(row)
            data[0] = left

        if isinstance(right, str):
            name = right
            right = curves[right].get(row+1)
            data[1] = right

        if name is not None:
            name = f"T{row}-{name}"

        logger.warning(f"table: {data}")
        return super().get_element(row, keyword, data, name=name)
