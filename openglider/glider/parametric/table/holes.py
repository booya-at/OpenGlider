from openglider.glider.parametric.table.elements import ElementTable

from openglider.glider.rib.elements import RibHole, RibSquareHole, MultiSquareHole

import logging

logger = logging.getLogger(__name__)

class HolesTable(ElementTable):
    keywords = [
        ("HOLE", 2),
        ("QUERLOCH", 2),
        ("HOLE5", 5),  # pos, width, height, vertical shift, rotation 
        ("HOLESQ", 3),
        ("HOLESQMULTI", 5)  # start, end, height, num_holes, border_width
    ]
    
    def get_element(self, keyword, data):
        if keyword in ("HOLE", "QUERLOCH"):
            return RibHole(data[0], data[1])
        
        elif keyword == "HOLESQ":
            return RibSquareHole(*data)
        elif keyword == "HOLESQMULTI":
            logger.info(str(data))
            return MultiSquareHole(*data)
        elif keyword == "HOLE5":
            size = [data[1], data[2]]

            return RibHole(data[0], size, vertical_shift=data[3], rotation=data[4])

        raise ValueError()