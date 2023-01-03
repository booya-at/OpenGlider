import logging
from openglider.gui.app.state.cache import Cache

from openglider.gui.qt import QtGui, QtCore, QtWidgets
from openglider.gui.app.app import GliderApp
from openglider.gui.views_2d.canvas import Canvas
from openglider.gui.views.compare.cell.graphics import GliderCellPlots, CellPlotLayers
from openglider.gui.views.compare.cell.settings import CellCompareSettings
from openglider.glider.project import GliderProject

logger = logging.getLogger(__name__)


class CellCache(Cache[GliderProject, GliderCellPlots]):
    def get_object(self, element: str) -> GliderCellPlots:
        project = self.elements[element]
        return GliderCellPlots(project.element, color=project.color)


class CellView(QtWidgets.QWidget):
    grid = True

    def __init__(self, app: GliderApp) -> None:
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.app = app

        self.settings_widget = CellCompareSettings(self)
        self.layout().addWidget(self.settings_widget)
        self.settings_widget.changed.connect(self.update)
        self.plot = Canvas()
        self.plot.locked_aspect_ratio = True
        self.plot.grid = self.grid
        self.plot.static = False
        self.plot.update_data()
        #self.plot.setBackground(None)
        self.layout().addWidget(self.plot.get_widget())

        self.cache = CellCache(app.state.projects)

        #self.arc_cache = ArcPlotCache(app)

    def update(self) -> None:
        self.plot.clear()

        selected =self.app.state.projects.get_selected()
        if selected:
            self.settings_widget.update_reference(selected)
        
        active = self.cache.get_update().active

        config = self.settings_widget.config
        for plots in active:
            dwg = plots.get(config.cell_no, config.layers)
            self.plot.addItem(dwg)
        
        self.plot.update()
