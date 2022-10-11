from typing import Any, List, Optional

from openglider.glider.parametric.table.elements import ElementTable, Keyword, TableType
from openglider.materials import cloth, Material

import logging

logger = logging.getLogger(__name__)



class CellClothTable(ElementTable):
    table_type = TableType.cell
    keywords = {
        "MATERIAL": Keyword([("Name", str)], target_cls=Material)
    }

    def get_element(self, row: int, keyword: str, data: List[Any], **kwargs: Any) -> Optional[Material]:
        name = data[0]

        if name == "empty":
            return None
        else:
            return cloth.get(data[0])


class RibClothTable(CellClothTable):
    table_type = TableType.rib
