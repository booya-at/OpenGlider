from openglider.utils.table import Table
from openglider.glider.parametric.table.elements import ElementTable
from openglider.glider.cell.elements import DiagonalRib, TensionLine, TensionStrap

import logging

logger = logging.getLogger(__name__)

class DiagonalTable(ElementTable):

    def __init__(self, table: Table, file_version: int=None):
        if file_version == 1:
            pass
            # height (0,1) -> (-1,1)
            # TODO
            #height1 = height1 * 2 - 1
            #height2 = height2 * 2 - 1

        super().__init__(table)


    keywords = [
        ("QR", 6),  # left, right, height, num_holes, border_width
    ]
    
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
    keywords = [
        ("STRAP", 3),  # left, right, width
        ("VEKTLAENGE", 2) # left, right
    ]
    
    def get_element(self, row, keyword, data, curves):
        left = data[0]
        right = data[1]

        if isinstance(left, str):
            left = curves[left].get(row)

        if isinstance(right, str):
            right = curves[right].get(row+1)

        if keyword == "STRAP":
            return TensionStrap(left, right, data[2])
        elif keyword == "VEKTLAENGE":
            return TensionLine(left, right)

        raise ValueError()