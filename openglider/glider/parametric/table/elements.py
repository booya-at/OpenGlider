import typing
from typing import Optional, TypeVar, Generic, Union
import logging
import enum

from attr import attrib

from openglider.utils.table import Table

logger = logging.getLogger(__name__)


ElementType = TypeVar("ElementType")

class TableType(enum.Enum):
    rib = "Rib Table"
    cell = "Cell Table"
    general = "General Table"


KeywordsType = list[Union[tuple[str, typing.Any], str]]

class Keyword:
    NoneType = typing.Any
    def __init__(self, attributes: Optional[KeywordsType]=None, description="", target_cls=None):
        if attributes is None:
            if target_cls is not None:
                attributes = list(typing.get_type_hints(target_cls.__init__).keys())
            else:
                raise ValueError(f"invalid configuration for Keyword: {self}")

        self.attributes: list[tuple[str, typing.Any]] = []
        annotations = {}
        if target_cls:
            annotations = typing.get_type_hints(target_cls.__init__)

        for attribute in attributes:
            if isinstance(attribute, str):
                attribute_name = attribute
                attribute_type = annotations.get(attribute, self.NoneType)
            else:
                attribute_name, attribute_type = attribute

            if attribute_type is self.NoneType:
                logger.debug(f"invalid type for {attribute}: {attribute_type} {type(attribute_type)} ({target_cls})")
            
            self.attributes.append((attribute_name, attribute_type))

        self.description = description
        self.target_cls = target_cls
    
    @property
    def attribute_length(self):
        return len(self.attributes)
    
    def get_attribute_names(self) -> typing.Iterable[str]:
        for name, dtype in self.attributes:
            yield f"{name}: {dtype.__name__}"
    
    def describe(self) -> str:
        description = f"  * length: {self.attribute_length}"
        if self.attributes:
            description += f"\n  * attributes: "
            description += ", ".join(self.get_attribute_names())
        if self.description:
            description += f"\n  * description: {self.description}"
        
        return description
    
    def get_header(self, name: str) -> Table:
        # TODO: move the name into the keyword
        table = Table()
        table[0, 0] = name
        for i, attribute in enumerate(self.get_attribute_names()):
            table[1, i] = attribute

        return table

    def get(self, keyword: str, data: list[typing.Any]):
        init_kwargs = {}

        for (name, target_type), value in zip(self.attributes, data):
            if target_type != self.NoneType and not isinstance(value, target_type):
                logger.warning(f"wrong type: {keyword}/{name}: {value}")
                value = target_type(value)
            
            init_kwargs[name] = value

        return self.target_cls(**init_kwargs)


class ElementTable(Generic[ElementType]):
    table_type: TableType = TableType.general
    keywords: dict[str, Keyword] = {}

    def __init__(self, table: Table=None):
        self.table = Table()
        if table and table[0, 0] is not None and table[0, 0] < "V4":
            _table = table.get_rows(0, 1)
            _table.append_bottom(table.get_rows(1, table.num_rows), space=1)
            _table[0, 0] = "V4"
        else:
            _table = table

        if _table is not None:
            for keyword in self.keywords:
                data_length = self.keywords[keyword].attribute_length
                for column in self.get_columns(table, keyword, data_length):
                    self.table.append_right(column)
    
    def __json__(self):
        return {
            "table": self.table
        }
    
    @classmethod
    def get_columns(cls, table: Table, keyword, data_length) -> list[Table]:
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
    
    def get(self, row_no: int, keywords=None, **kwargs) -> list[ElementType]:
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
                    except Exception as e:
                        raise ValueError(f"failed to get element ({keyword}: {row_no-2}, ({data}) {e}") from e
                        
                    elements.append(element)
        
        return elements
    
    def get_one(self, row_no: int, keywords=None, **kwargs):
        elements = self.get(row_no, keywords=keywords, **kwargs)

        if len(elements) > 1:
            logger.error(f"too many elements in row {row_no}! {elements}")

        if len(elements) > 0:
            return elements[0]
        
        return None
    
    def get_element(self, row: int, keyword: str, data: list[typing.Any], **kwargs) -> ElementType:
        keyword_mapper = self.keywords[keyword]

        return keyword_mapper.get(keyword, data)

    def _repr_html_(self):
        return self.table._repr_html_()


class CellTable(ElementTable):
    table_type = TableType.cell

class RibTable(ElementTable):
    table_type = TableType.rib
