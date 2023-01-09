from typing import Dict, List
import datetime
import logging
import pyqtgraph
from openglider.gui.qt import QtWidgets

from openglider.glider.project import GliderProject
from openglider.gui.app.app import GliderApp
from openglider.utils.table import Table
from openglider.gui.widgets.table import QTable
from openglider.gui.state.glider_list import GliderCache

logger = logging.getLogger(__name__)


class TableCache(GliderCache[Table]):
    def get_object(self, name: str) -> Table:
        project = self.elements[name]
        table = project.element.get_data_table()
        return table


class GliderTable(QTable):
    def __init__(self, app: GliderApp, parent: QtWidgets.QWidget=None):
        super().__init__(parent)
        self.app = app
        self.cache = TableCache(app.state.projects)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
    
    def update(self) -> None:
        table = Table()
        
        for i, active_project_table in enumerate(self.cache.get_update().active):
            if i == 0:
                start = 0
            else:
                start = 1
            table.append_right(active_project_table.get_columns(start,2))
        
        self.clear()
        self.push_table(table)
        self.resizeColumnsToContents()
