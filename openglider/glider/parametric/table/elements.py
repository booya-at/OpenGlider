from typing import List, Tuple

from openglider.utils.table import Table


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
    def get_columns(table: Table, keyword, data_length):
        columns = []
        column = 0
        while column < table.num_columns:
            if table[0, column] == keyword:
                columns.append(table.get_columns(column, column+data_length))
                
                column += data_length
            else:
                column += 1

        return columns
    
    def get(self, row_no):
        row_no += 1  # skip header line
        elements = []
        for keyword, data_length in self.keywords:
            for column in self.get_columns(self.table, keyword, data_length):
                if column[row_no, 0] is not None:
                    elements.append(self.get_element(keyword, [column[row_no, i] for i in range(data_length)]))
        
        return elements
    
    def get_element(self, keyword, data):
        raise NotImplementedError()

    def _repr_html_(self):
        return self.table._repr_html_()
