from typing import Optional

from openglider.glider.parametric.table.elements import ElementTable, Keyword, TableType
from openglider.materials import cloth, Material

import logging

logger = logging.getLogger(__name__)



class CellClothTable(ElementTable):
    table_type = TableType.cell
    keywords = {
        "MATERIAL": Keyword(["Name"])
    }

    def get_element(self, row, keyword, data, **kwargs) -> Optional[Material]:
        name = data[0]

        if name == "empty":
            return None
        else:
            return cloth.get(data[0])


class RibClothTable(ElementTable):
    table_type = TableType.rib
    keywords = {
        "MATERIAL": Keyword(["Name"])
    }

    def get_element(self, row, keyword, data, **kwargs) -> Optional[Material]:
        name = data[0]

        if name == "empty":
            return None
        else:
            return cloth.get(data[0])
