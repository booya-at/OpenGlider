import enum
import logging
import sys
import typing
from typing import Any, Callable, Generic, TypeVar


from openglider.glider.curve import GliderCurveType
from openglider.glider.parametric.table.base.dto import DTO
from openglider.glider.parametric.table.base.parser import Parser
from openglider.utils.table import Table
from openglider.vector.unit import Quantity

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
    dtos: dict[str, type[DTO]] = {}

    def __init__(self, table: Table=None, migrate_header: bool=False):
        self.table = Table()
        if table is not None:
            if migrate_header:
                _table = table.get_rows(0, 1)
                _table.append_bottom(table.get_rows(1, table.num_rows), space=1)
            else:
                _table = table

            if _table is not None:
                def add_data(keyword: str, data_length: int) -> None:
                    for column in self.get_columns(_table, keyword, data_length):
                        self.table.append_right(column)

                for keyword in self.keywords:
                    data_length = self.keywords[keyword].attribute_length
                    add_data(keyword, data_length)

                for dto in self.dtos:
                    data_length = self.dtos[dto].column_length()
                    add_data(dto, data_length)
    
    def __json__(self) -> dict[str, Any]:
        return {
            "table": self.table
        }
    
    @classmethod
    def get_columns(cls, table: Table, keyword: str, data_length: int) -> list[Table]:
        columns = []
        column = 0

        if keyword in cls.keywords:
            keyword_instance = cls.keywords[keyword]
            header = keyword_instance.get_header(keyword)
        elif keyword in cls.dtos:
            dto = cls.dtos[keyword]
            types = dto.describe()
            header = Table()
            header[0, 0] = keyword
            for i, (field_name, field_type) in enumerate(types):
                header[1, i] = f"{field_name}: {field_type}"

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
    
    def get(self, row_no: int, keywords: list[str] | None=None, **kwargs: Any) -> list[ElementType]:
        row_no += 2  # skip header line
        elements = []
        
        for keyword in list(self.keywords.keys()) + list(self.dtos.keys()):
            if keyword in self.keywords:
                data_length = self.keywords[keyword].attribute_length
            else:
                data_length = self.dtos[keyword].column_length()

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
    def get_curve_value(curves: dict[str, GliderCurveType] | None, curve_name: str | float, rib_no: int) -> float:
        if curves is None:
            raise ValueError("No curves specified")

        if isinstance(curve_name, str):
            factor = 1.
            if curve_name.startswith("-"):
                curve_name = curve_name[1:]
                factor = -1
            
            return curves[curve_name].get(rib_no) * factor
        
        return curve_name
    
    def get_one(self, row_no: int, keywords: list[str] | None=None, **kwargs: Any) -> ElementType | None:
        elements = self.get(row_no, keywords=keywords, **kwargs)

        if len(elements) > 1:
            logger.error(f"too many elements in row {row_no}! {elements}")

        if len(elements) > 0:
            return elements[0]
        
        return None

    def _prepare_dto_data(self, row: int, dto: type[DTO], data: list[Any], resolvers: list[Parser]) -> dict[str, Any]:
        fields = dto.__fields__.items()
        
        dct: dict[str, Any] = {}
        index = 0

        for field_name, field in fields:
            if dto._is_cell_tuple(field.type_):
                dct[field_name] = (
                    resolvers[row].parse(data[index]),
                    resolvers[row+1].parse(data[index+1])
                )
                index += 2
            else:
                if field.type_ == str:
                    dct[field_name] = data[index]
                else:
                    dct[field_name] = resolvers[row].parse(data[index])
                index += 1
        
        return dct

    
    def get_element(self, row: int, keyword: str, data: list[typing.Any], **kwargs: Any) -> ElementType:
        if keyword in self.keywords:
            keyword_mapper = self.keywords[keyword]

            return keyword_mapper.get(keyword, data)
        
        elif keyword in self.dtos:
            dto = self.dtos[keyword]            
            dct = self._prepare_dto_data(row, dto, data, kwargs["resolvers"])
                
            return dto(**dct).get_object()

        else:
            raise ValueError()

    def _repr_html_(self) -> str:
        return self.table._repr_html_()


class CellTable(ElementTable):
    table_type = TableType.cell

class RibTable(ElementTable):
    table_type = TableType.rib
