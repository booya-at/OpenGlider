import enum
import logging
import sys
import typing
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.table.base.parser import Parser
from openglider.utils.table import Table
from openglider.version import __version__

from .keyword import Keyword

logger = logging.getLogger(__name__)

ElementType = TypeVar("ElementType")

class TableType(enum.Enum):
    rib = "Rib Table"
    cell = "Cell Table"
    general = "General Table"

class ElementTable(Generic[ElementType]):
    table_type: TableType = TableType.general
    keywords: dict[str, Keyword] = {}

    def __init__(self, table: Table=None, migrate_header: bool=False):
        self.table = Table()
        if table is not None:
            if migrate_header:
                _table = table.get_rows(0, 1)
                _table.append_bottom(table.get_rows(1, table.num_rows), space=1)
            else:
                _table = table

            if _table is not None:
                for keyword in self.keywords:
                    data_length = self.keywords[keyword].attribute_length
                    for column in self.get_columns(_table, keyword, data_length):
                        self.table.append_right(column)
    
    def __json__(self) -> Dict[str, Any]:
        return {
            "table": self.table
        }
    
    @classmethod
    def get_columns(cls, table: Table, keyword: str, data_length: int) -> list[Table]:
        columns = []
        column = 0
        keyword_instance = cls.keywords[keyword]
        header = keyword_instance.get_header(keyword)

        while column < table.num_columns:
            if table[0, column] == keyword:
                columns_part_header = header.copy()
                columns_part = table.get_columns(column, column+data_length).get_rows(2, None)
                columns_part_header.append_bottom(columns_part)
                columns.append(columns_part_header)
                
                column += data_length
            else:
                column += 1

        return columns
    
    def get(self, row_no: int, keywords: List[str] | None=None, **kwargs: Any) -> list[ElementType]:
        row_no += 2  # skip header line
        elements = []
        
        for keyword in self.keywords:
            data_length = self.keywords[keyword].attribute_length

            if keywords is not None and keyword not in keywords:
                logger.debug(f"skipping keyword {keyword}")
                continue

            for column in self.get_columns(self.table, keyword, data_length):
                if column[row_no, 0] is not None:
                    data = [column[row_no, i] for i in range(data_length)]
                    try:
                        element = self.get_element(row_no-2, keyword, data, **kwargs)
                    except Exception:
                        _, value, traceback = sys.exc_info()
                        raise ValueError(f"failed to get element ({keyword}: {row_no-2}, ({data}) {value}").with_traceback(traceback)
                        
                    elements.append(element)
        
        return elements
    
    @staticmethod
    def get_curve_value(curves: Dict[str, GliderCurveType] | None, curve_name: str | float, rib_no: int) -> float:
        if curves is None:
            raise ValueError("No curves specified")

        if isinstance(curve_name, str):
            factor = 1.
            if curve_name.startswith("-"):
                curve_name = curve_name[1:]
                factor = -1
            
            return curves[curve_name].get(rib_no) * factor
        
        return curve_name
    
    def get_one(self, row_no: int, keywords: List[str] | None=None, **kwargs: Any) -> ElementType | None:
        elements = self.get(row_no, keywords=keywords, **kwargs)

        if len(elements) > 1:
            logger.error(f"too many elements in row {row_no}! {elements}")

        if len(elements) > 0:
            return elements[0]
        
        return None
    
    def get_element(self, row: int, keyword: str, data: list[typing.Any], **kwargs: Any) -> ElementType:
        keyword_mapper = self.keywords[keyword]

        return keyword_mapper.get(keyword, data)

    def _repr_html_(self) -> str:
        return self.table._repr_html_()


class CellTable(ElementTable):
    table_type = TableType.cell

class RibTable(ElementTable):
    table_type = TableType.rib
