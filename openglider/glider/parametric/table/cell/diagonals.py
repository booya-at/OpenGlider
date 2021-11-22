from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable, Keyword
from openglider.glider.cell.elements import DiagonalRib, TensionLine, TensionStrap

import logging

logger = logging.getLogger(__name__)

class DiagonalTable(ElementTable):

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

        if isinstance(left, str):
            left = curves[left].get(row)

        if isinstance(right, str):
            right = curves[right].get(row+1)


        if keyword == "QR":
            height1 = data[4]
            height2 = data[5]

            left_front = (left - data[2] / 2, height1)
            left_back = (left + data[2] / 2, height1)
            right_front = (right - data[3] / 2, height2)
            right_back = (right + data[3] / 2, height2)

            return DiagonalRib(left_front, left_back, right_front, right_back)

        raise ValueError()


class StrapTable(ElementTable):
    keywords = {
        "STRAP": Keyword(["left", "right", "width"], target_cls=TensionStrap),  # left, right, width
        "VEKTLAENGE": Keyword(["left", "right"], target_cls=TensionLine)
    }
    
    def get_element(self, row, keyword, data, curves):
        left = data[0]
        right = data[1]

        if isinstance(left, str):
            left = curves[left].get(row)
            data[0] = left

        if isinstance(right, str):
            right = curves[right].get(row+1)
            data[1] = right

        return super().get_element(row, keyword, data)
