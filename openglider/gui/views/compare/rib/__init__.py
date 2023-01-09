import logging
from openglider.gui.state.glider_list import GliderCache

from openglider.gui.qt import QtWidgets
from openglider.gui.app.app import GliderApp
from openglider.gui.views_2d.canvas import Canvas
from openglider.gui.views.compare.rib.graphics import GliderRibPlots
from openglider.gui.views.compare.rib.settings import RibCompareSettings


logger = logging.getLogger(__name__)


class RibCache(GliderCache[GliderRibPlots]):
    def get_object(self, element: str) -> GliderRibPlots:
        project = self.elements[element]
        return GliderRibPlots(project.element, color=project.color)


class RibView(QtWidgets.QWidget):
    grid = False

    def __init__(self, app: GliderApp):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.app = app

        self.settings_widget = RibCompareSettings(self)
        self.layout().addWidget(self.settings_widget)
        self.settings_widget.changed.connect(self.update)
        self.plot = Canvas()
        self.plot.locked_aspect_ratio = True
        self.plot.grid = self.grid
        self.plot.static = False
        self.plot.update_data()
        #self.plot.setBackground(None)
        self.layout().addWidget(self.plot.get_widget())

        self.cache = RibCache(app.state.projects)

    def update(self) -> None:
        self.plot.clear()

        selected = self.app.state.projects.get_selected()
        if selected:
            self.settings_widget.update_reference(selected)

        update = self.cache.get_update()
        active = update.active

        config = self.settings_widget.config
        for plots in active:
            dwg = plots.get(config.rib_no, config.layers)
            self.plot.addItem(dwg)
        
        self.plot.update()
