from typing import Optional

from openglider.glider.parametric.table.elements import ElementTable, Keyword
from openglider.materials import cloth, Material

import logging

logger = logging.getLogger(__name__)



class ClothTable(ElementTable):
    keywords = {
        "MATERIAL": Keyword(["Name"])
    }

    def get_element(self, row, keyword, data, **kwargs) -> Optional[Material]:
        name = data[0]

        if name == "empty":
            return None
        else:
            return cloth.get(data[0])
