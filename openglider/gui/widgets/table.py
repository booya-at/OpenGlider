from openglider.gui.qt import QtWidgets, QtCore

import openglider.utils.table


class QTable(QtWidgets.QTableWidget):
    def __init__(self, parent: QtWidgets.QWidget=None, table: openglider.utils.table.Table=None, readonly: bool=True):
        self.readonly = readonly
        super().__init__(parent=parent)

        if table is not None:
            self.push_table(table)

    def push_table(self, table: openglider.utils.table.Table) -> None:
        self.setColumnCount(table.num_columns)
        self.setRowCount(table.num_rows)

        for row_no in range(table.num_rows):
            for column_no in range(table.num_columns):
                value = table[row_no, column_no]

                if type(value) is float:
                    text = f"{value:.3f}"
                elif value is None:
                    text = ""
                else:
                    text = str(value)
                
                item = self.item(row_no, column_no)
                if item is None:
                    item = QtWidgets.QTableWidgetItem()
                    self.setItem(row_no, column_no, item)
                
                item.setText(text)
                if self.readonly:
                    item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable)

    def get_table(self) -> openglider.utils.table.Table:
        table = openglider.utils.table.Table()

        for row_no in range(self.rowCount()):
            for column_no in range(self.columnCount()):
                table[(row_no, column_no)] = self.item(row_no, column_no).text()

        return table

