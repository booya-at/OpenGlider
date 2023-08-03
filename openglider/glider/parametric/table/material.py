from typing import Any

from openglider.glider.parametric.table.base import ElementTable, Keyword, TableType
from openglider.materials import cloth, Material

import logging

logger = logging.getLogger(__name__)



class CellClothTable(ElementTable):
    table_type = TableType.cell
    keywords = {
        "MATERIAL": Keyword([("Name", str)], target_cls=Material)
    }

    def get_element(self, row: int, keyword: str, data: list[Any], **kwargs: Any) -> Material | None:
        name = data[0]

        if name == "empty":
            return None
        else:
            return cloth.get(data[0])


class RibClothTable(CellClothTable):
    table_type = TableType.rib
