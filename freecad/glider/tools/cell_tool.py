from __future__ import division

from pivy import coin

from PySide import QtGui

from .glider import draw_glider, draw_lines
from .tools import BaseTool, input_field
from .table import base_table_widget


def refresh():
    """Compatibility hook for the workbench refresh entry point."""
    pass


class CellTool(BaseTool):
    """Task panel tool for editing cell-related features.

    Provides access to diagonals and vector straps defined on the
    :class:`ParametricGlider` and previews the resulting 3D glider and
    lines in a dedicated view.
    """

    hide = True
    turn = False

    def __init__(self, obj):
        """Create the cell tool for the given FreeCAD glider object."""
        super(CellTool, self).__init__(obj)
        self.diagonals_table = diagonals_table()
        self.diagonals_table.get_from_ParametricGlider(self.parametric_glider)
        self.diagonals_button = QtGui.QPushButton("diagonals")
        self.diagonals_button.clicked.connect(self.diagonals_table.show)
        self.layout.setWidget(0, input_field, self.diagonals_button)

        self.vector_table = vector_table()
        self.vector_table.get_from_ParametricGlider(self.parametric_glider)
        self.vector_button = QtGui.QPushButton("vector strap")
        self.vector_button.clicked.connect(self.vector_table.show)
        self.layout.setWidget(1, input_field, self.vector_button)

        self.update_button = QtGui.QPushButton("update glider")
        self.update_button.clicked.connect(self.update_glider)
        self.layout.setWidget(2, input_field, self.update_button)
        self.draw_glider()

    def draw_glider(self):
        """Draw a preview of the 3D glider and its lines in the task view."""
        _rot = coin.SbRotation()
        _rot.setValue(coin.SbVec3f(0, 1, 0), coin.SbVec3f(1, 0, 0))
        rot = coin.SoRotation()
        rot.rotation.setValue(_rot)
        self.task_separator += rot
        draw_glider(
            self.parametric_glider.get_glider_3d(),
            self.task_separator,
            hull=None,
            ribs=True,
            fill_ribs=False,
        )
        draw_lines(
            self.parametric_glider.get_glider_3d(),
            vis_lines=self.task_separator,
            line_num=1,
        )

    def update_glider(self):
        """Apply table changes and redraw the glider preview."""
        self.task_separator.removeAllChildren()
        self.apply_elements()
        self.draw_glider()

    def apply_elements(self):
        """Write current table contents back to the ParametricGlider."""
        self.diagonals_table.apply_to_glider(self.parametric_glider)
        self.vector_table.apply_to_glider(self.parametric_glider)

    def accept(self):
        """Accept changes, close tables and update the main view glider."""
        super(CellTool, self).accept()
        self.diagonals_table.hide()
        self.vector_table.hide()
        del self.diagonals_table
        del self.vector_table
        self.update_view_glider()

    def reject(self):
        """Discard changes and close helper tables."""
        super(CellTool, self).reject()
        self.diagonals_table.hide()
        self.vector_table.hide()
        del self.diagonals_table
        del self.vector_table


def number_input(number):
    """Create a table item with a numeric value represented as text."""
    return QtGui.QTableWidgetItem(str(number))


class diagonals_table(base_table_widget):
    """Table widget for configuring diagonal ribs between cells."""

    name = "diagonals"
    keyword = "diagonals"

    def __init__(self):
        """Initialise the diagonals table with default headers."""
        super(diagonals_table, self).__init__(name="diagonals")
        self.table.setRowCount(200)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "right\nfront",
                "rf\nheight",
                "right\nback",
                "rb\nheight",
                "left\nback",
                "lb\nheight",
                "left\nfront",
                "lf\nheight",
                "cells",
            ]
        )

    def get_from_ParametricGlider(self, ParametricGlider):
        """Populate the table from existing diagonals on the glider."""
        if "diagonals" in ParametricGlider.elements:
            diags = ParametricGlider.elements["diagonals"]
            for row, element in enumerate(diags):
                entries = list(
                    element["right_front"]
                    + element["right_back"]
                    + element["left_back"]
                    + element["left_front"]
                )
                entries.append(element["cells"])
                self.table.setRow(row, entries)

    def apply_to_glider(self, ParametricGlider):
        """Write the current table contents back to the diagonals list."""
        num_rows = self.table.rowCount()
        # remove all diagonals from the glider_2d
        ParametricGlider.elements[self.keyword] = []
        for n_row in range(num_rows):
            row = self.get_row(n_row)
            if row:
                diagonal = {}
                diagonal["right_front"] = (row[0], row[1])
                diagonal["right_back"] = (row[2], row[3])
                diagonal["left_back"] = (row[4], row[5])
                diagonal["left_front"] = (row[6], row[7])
                diagonal["cells"] = row[-1]
                ParametricGlider.elements["diagonals"].append(diagonal)

    def get_row(self, n_row):
        """Return a parsed diagonal definition from the given row or ``None``."""
        str_row = [
            self.table.item(n_row, i).text()
            for i in range(9)
            if self.table.item(n_row, i)
        ]
        str_row = [item for item in str_row if item != ""]
        if len(str_row) != 9:
            return None
        try:
            return list(map(float, str_row[:-1])) + [
                list(map(int, str_row[-1].split(",")))
            ]
        except TypeError as e:
            print(e)
            print("something wrong with row " + str(n_row))
            return None


class vector_table(base_table_widget):
    """Table widget for configuring tension lines / vector straps."""

    def __init__(self):
        """Initialise the vector strap table with default headers."""
        super(vector_table, self).__init__(name="vector straps")
        self.table.setRowCount(200)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["left", "right", "cells"])

    def get_from_ParametricGlider(self, ParametricGlider):
        """Populate the table from existing tension lines on the glider."""
        if "tension_lines" in ParametricGlider.elements:
            tension_lines = ParametricGlider.elements["tension_lines"]
            for row, element in enumerate(tension_lines):
                entries = [element["right"], element["left"]]
                entries.append(element["cells"])
                self.table.setRow(row, entries)

    def apply_to_glider(self, ParametricGlider):
        """Write the current table contents back to ``tension_lines``."""
        num_rows = self.table.rowCount()
        # remove all diagonals from the glide_2d
        ParametricGlider.elements["tension_lines"] = []
        for n_row in range(num_rows):
            row = self.get_row(n_row)
            if row:
                strap = {}
                strap["right"] = row[0]
                strap["left"] = row[1]
                strap["cells"] = row[2]
                ParametricGlider.elements["tension_lines"].append(strap)

    def get_row(self, n_row):
        """Return a parsed vector strap definition from the given row."""
        str_row = [
            self.table.item(n_row, i).text()
            for i in range(3)
            if self.table.item(n_row, i)
        ]

        str_row = [item for item in str_row if item != ""]
        if len(str_row) != 3:
            return None
        try:
            return list(map(float, str_row[:-1])) + [
                list(map(int, str_row[-1].split(",")))
            ]
        except TypeError as e:
            print("something wrong with row " + str(n_row))
            return None
