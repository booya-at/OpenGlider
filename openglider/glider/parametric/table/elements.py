from typing import List, Tuple, Any
import logging

from openglider.utils.table import Table

logger = logging.getLogger(__name__)

class ElementTable:
    keywords: List[Tuple[str, int]] = []

    def __init__(self, table: Table):
        self.table = Table()

        for keyword, data_length in self.keywords:
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
    
    def get(self, row_no: int) -> List[Any]:
        row_no += 1  # skip header line
        elements = []
        for keyword, data_length in self.keywords:
            for column in self.get_columns(self.table, keyword, data_length):
                if column[row_no, 0] is not None:
                    elements.append(self.get_element(row_no-1, keyword, [column[row_no, i] for i in range(data_length)]))
        
        return elements
    
    def get_element(self, row: int, keyword, data) -> Any:
        raise NotImplementedError()

    def _repr_html_(self):
        return self.table._repr_html_()
