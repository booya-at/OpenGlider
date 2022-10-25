import logging
from typing import Dict

from openglider.gui.app.app import GliderApp
from openglider.gui.views.compare.aoa import AoAView
from openglider.gui.views.compare.arc import ArcView
from openglider.gui.views.compare.cell import CellView
from openglider.gui.views.compare.data import GliderTable
from openglider.gui.views.compare.glider_3d import Glider3DView
from openglider.gui.views.compare.rib import RibView
from openglider.gui.views.compare.shape import ShapeView
from openglider.gui.qt import QtWidgets

logger = logging.getLogger(__name__)

class GliderPreview(QtWidgets.QWidget):
    tabs_widget: QtWidgets.QTabWidget
    tabs: Dict[str, QtWidgets.QWidget]

    def __init__(self, app: GliderApp):
        super().__init__()
        self.app = app

        self.setLayout(QtWidgets.QHBoxLayout())
        self.tabs_widget = QtWidgets.QTabWidget(self)

        self.tabs = {
            "Shape": ShapeView(app),
            "Arc": ArcView(app),
            "AoA": AoAView(app),
            "Ribs": RibView(app),
            "Cells": CellView(app),
            "Table": GliderTable(app),
            "3D": Glider3DView(app)
        }
        self.tab_names = list(self.tabs.keys())

        for name, widget in self.tabs.items():
            self.tabs_widget.addTab(widget, name)

        self.tabs_widget.currentChanged.connect(self.set_tab)
        self.layout().addWidget(self.tabs_widget)


        #self._layout.addWidget(self.buttons, 0, 1)

        self.update()
    
    def get_active_view_name(self):
        index = self.tabs_widget.currentIndex()
        name = self.tab_names[index]
        return name

    
    def set_tab(self):
        name = self.get_active_view_name()
        self.app.state.current_preview = name
        self.update()

    def update(self):
        if not self.app.state.current_preview:
            name = self.get_active_view_name()
            if name:
                self.app.state.current_preview = name
            else:
                return

        if self.app.state.current_preview != self.get_active_view_name():
            if self.app.state.current_preview in self.tab_names:
                self.tabs_widget.setCurrentIndex(self.tab_names.index(self.app.state.current_preview))

        self.tabs_widget.currentWidget().update()
