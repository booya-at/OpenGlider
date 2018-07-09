from __future__ import division
from PySide import QtCore, QtGui
from ._tools import BaseTool, text_field, input_field


def refresh():
    pass


class table_tool(BaseTool):
    hide = False
    def __init__(self, obj):
        super(table_tool, self).__init__(obj)

        self.table_widget = base_table_widget()
        self.table_button = QtGui.QPushButton('table')
        self.table_button.clicked.connect(self.table_widget.show)
        self.layout.setWidget(0, input_field, self.table_button)

        self.table_widget_1 = base_table_widget()
        self.table_button_1 = QtGui.QPushButton('table')
        self.table_button_1.clicked.connect(self.table_widget_1.show)
        self.layout.setWidget(1, input_field, self.table_button_1)


class base_table_widget(QtGui.QWidget):
    '''a table which is shown infront of the mainwindow'''
    instances = []
    _last_pos = None
    name = "test"

    @classmethod
    def hide_all(cls):
        for obj in cls.instances:
            obj.hide()

    def __init__(self, parent=None, name='test'):
        base_table_widget.instances.append(self)
        super(base_table_widget, self).__init__(parent)
        self.layout = QtGui.QVBoxLayout()
        self.table = base_table(self)
        self.setLayout(self.layout)
        label = QtGui.QLabel(name)
        label.setFont(QtGui.QFont('Arial', 20))
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(label)
        self.layout.addWidget(self.table)
        self.setWindowFlags(QtCore.Qt.Window |
                            QtCore.Qt.WindowStaysOnTopHint)
        self.move(*self.desktop_size)

    def closeEvent(self, *attr):
        self.hide()

    def show(self):
        if self.isHidden():
            base_table_widget.hide_all()
            super(base_table_widget, self).show()
            if base_table_widget._last_pos:
                self.move(base_table_widget._last_pos)
        else:
            self.hide()

    @property
    def apply_widget(self):
        layout = QtGui.QHBoxLayout()
        widget = QtGui.QWidget()
        widget.setLayout(layout)
        accept_button = QtGui.QPushButton('Ok')
        reject_button = QtGui.QPushButton('Cancel')
        accept_button.clicked.connect(self.accept)
        reject_button.clicked.connect(self.reject)
        layout.addWidget(accept_button)
        layout.addWidget(reject_button)
        return widget

    def accept(self):
        self.hide()

    def reject(self):
        self.hide()

    @property
    def desktop_size(self):
        d = QtGui.QApplication.desktop()
        return ((d.width() - self.width()) / 2,
                (d.height() - self.height()) / 2)

    def test_init(self):
        self.table.setRowCount(10)
        self.table.setColumnCount(10)

    def hide(self, hide=True):
        if not self.isHidden():
            base_table_widget._last_pos = self.pos()
            if hide:
                super(base_table_widget, self).hide()


class base_table(QtGui.QTableWidget):
    def __init__(self, parent=None):
        super(base_table, self).__init__(parent)
        # self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Stretch)

    @property
    def table_width(self):
        w = (self.contentsMargins().left() +
             self.contentsMargins().right() +
             self.verticalHeader().width())
        for i in range(self.columnCount()):
            w += self.columnWidth(i)
        return w

    @property
    def table_height(self):
        h = (self.contentsMargins().top() +
             self.contentsMargins().bottom() +
             self.horizontalHeader().height())
        for i in range(self.rowCount()):
            h += self.rowHeight(i)
        return h

    def sizeHint(self):
        return QtCore.QSize(self.table_width, self.table_height)

    def setItem(self, row, col, entry):
        if hasattr(entry,'__iter__') and not isinstance(entry, str):
            entry = str(entry)[1:-1]
        else:
            entry = str(entry)
        super(base_table, self).setItem(row, col, QtGui.QTableWidgetItem(entry))

    def setRow(self, row, items, start=0):
        for col, item in enumerate(items):
            self.setItem(row, col + start, item)
