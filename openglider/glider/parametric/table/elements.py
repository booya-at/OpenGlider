from typing import List, Tuple, Any, Optional, TypeVar, Generic, Dict
import logging
import enum

from openglider.utils.table import Table

logger = logging.getLogger(__name__)


ElementType = TypeVar("ElementType")

class TableType(enum.Enum):
    rib = "Rib Table"
    cell = "Cell Table"
    general = "General Table"


class Keyword:
    def __init__(self, attributes=None, attribute_length=None, description="", target_cls=None):
        if attributes is None and attribute_length is None:
            raise ValueError(f"invalid configuration for Keyword: {self}")

        self.attributes = attributes
        self._attribute_length = attribute_length
        self.description = description
        self.target_cls = target_cls
    
    @property
    def attribute_length(self):
        if self.attributes:
            return len(self.attributes)
        
        return self._attribute_length
    
    def describe(self) -> str:
        description = f"  * length: {self.attribute_length}"
        if self.attributes:
            description += f"\n  * attributes: {self.attributes} "
        if self.description:
            description += f"\n  * description: {self.description}"
        
        return description


class ElementTable(Generic[ElementType]):
    table_type: TableType = TableType.general
    keywords: Dict[str, Keyword] = {}

    def __init__(self, table: Table=None):
        self.table = Table()

        if table is not None:
            for keyword in self.keywords:
                data_length = self.keywords[keyword].attribute_length
                for column in self.get_columns(table, keyword, data_length):
                    self.table.append_right(column)
    
    def __json__(self):
        return {
            "table": self.table
        }
    
    @staticmethod
    def get_columns(table: Table, keyword, data_length) -> List[Table]:
        columns = []
        column = 0
        while column < table.num_columns:
            if table[0, column] == keyword:
                columns.append(table.get_columns(column, column+data_length))
                
                column += data_length
            else:
                column += 1

        return columns
    
    def get(self, row_no: int, keywords=None, **kwargs) -> List[ElementType]:
        row_no += 1  # skip header line
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
                        element = self.get_element(row_no-1, keyword, data, **kwargs)
                    except Exception as e:
                        raise ValueError(f"failed to get element ({keyword}: {row_no-1}, ({data}) {e}")
                        
                    elements.append(element)
        
        return elements
    
    def get_element(self, row: int, keyword: str, data: List[Any], **kwargs) -> ElementType:
        keyword_mapper = self.keywords[keyword]

        if keyword_mapper.target_cls is None:
            raise NotImplementedError(f"No target Class defined for keyword: {keyword}")
        if keyword_mapper.attributes is None:
            raise NotImplementedError(f"No attributes defined on keyword: {keyword}")

        init_kwargs = {
            name: value for name, value in zip(keyword_mapper.attributes, data)
        }

        target_cls = keyword_mapper.target_cls

        if hasattr(target_cls, "__anotations__"):
            for key, target_type in target_cls.__annotations__.items():
                value = init_kwargs[key]
                if not isinstance(value, target_type):
                    logger.warning(f"wrong type: {keyword}/{key}: {value}")
                    init_kwargs[key] = target_type(value)

        return keyword_mapper.target_cls(**init_kwargs)


    def _repr_html_(self):
        return self.table._repr_html_()


class CellTable(ElementTable):
    table_type = TableType.cell

class RibTable(ElementTable):
    table_type = TableType.rib
