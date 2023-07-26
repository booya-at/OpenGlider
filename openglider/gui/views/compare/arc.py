from typing import Dict, List
import datetime
import pyqtgraph
import logging
from openglider.gui.qt import QtGui, QtCore, QtWidgets
from openglider.glider.project import GliderProject
from openglider.gui.app.app import GliderApp
from openglider.gui.views_2d.canvas import Canvas
from openglider.gui.views_2d.arc import Arc2D
from openglider.gui.state.glider_list import GliderCache

from openglider.gui.views.compare.base import CompareView

logger = logging.getLogger(__name__)


class ArcPlotCache(GliderCache[Arc2D]):
    def get_object(self, name: str) -> Arc2D:
        project = self.elements[name]
        return Arc2D(project.element, color=project.color)


class ArcView(CompareView):
    grid = False

    def __init__(self, app: GliderApp):
        super().__init__()
        self.setLayout(QtWidgets.QHBoxLayout())
        self.app = app

        self.plot = Canvas()
        self.plot.locked_aspect_ratio = True
        self.plot.grid = self.grid
        self.plot.static = True
        self.plot.update_data()
        #self.plot.setBackground(None)
        self.layout().addWidget(self.plot.get_widget())

        self.arc_cache = ArcPlotCache(app.state.projects)

    def update_view(self) -> None:
        changeset = self.arc_cache.get_update()

        for plt in changeset.removed:
            self.plot.removeItem(plt)

        for plt in changeset.added:
            self.plot.addItem(plt)
        
        self.plot.update()
