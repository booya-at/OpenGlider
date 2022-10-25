from openglider.gui.qt import QtWidgets, QtGui

from openglider_physics.gui.wizzards.base import Wizard
from openglider.gui.widgets import QTable, Slider

class LineForceView(Wizard):
    def __init__(self, app, project):
        super().__init__(app, project)

        self.line_force_table = QTable()
        self.setLayout(QtWidgets.QGridLayout())
        self.layout().addWidget(self.line_force_table, 0, 0)

        self.project.glider_3d.lineset.iterate_target_length()

        line_table = self.project.glider_3d.lineset.get_table()
        line_table[0, line_table.num_columns] = ""  # insert empty column
        line_table.append_right(self.project.glider_3d.lineset.get_force_table())
        
        self.line_force_table.push_table(line_table)