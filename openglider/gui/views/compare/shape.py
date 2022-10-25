import datetime
import enum
import logging
from typing import Dict, List, Tuple
from openglider.gui.app.state.cache import Cache

import pyqtgraph
from openglider.glider.project import GliderProject
from openglider.gui.app.app import GliderApp
from openglider.gui.views_2d.canvas import Canvas, LayoutGraphics
from openglider.gui.widgets.select import EnumSelection
from openglider.plots.sketches.shapeplot import ShapePlot, ShapePlotConfig
from openglider.utils.colors import Color
from openglider.gui.qt import QtCore, QtGui, QtWidgets
from openglider.gui.widgets.flow_layout import FlowLayout

logger = logging.getLogger(__name__)


class ScaleOptions(enum.Enum):
    none = "No scaling"
    span = "Span"
    area = "Area"


class ShapeConfigWidget(QtWidgets.QWidget):
    reference_area: float=1.
    reference_span: float=1.

    changed = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.config = ShapePlotConfig()

        self.setLayout(FlowLayout())

        self.checkboxes = {}

        def get_clickhandler(prop):
            
            def toggle_prop(value):
                setattr(self.config, prop, value)
                self.changed.emit()
            
            return toggle_prop

        for prop in self.config.view_layers():

            checkbox = QtWidgets.QCheckBox(self)
            checkbox.setChecked(getattr(self.config, prop))
            checkbox.setText(f"{prop}")
            checkbox.clicked.connect(get_clickhandler(prop))
            self.layout().addWidget(checkbox)
            self.checkboxes[prop] = checkbox
        
        self.selection = EnumSelection(ScaleOptions)
        self.selection.changed.connect(self.update_scale)
        self.layout().addWidget(self.selection)

    def get_config(self) -> Tuple[ShapePlotConfig, ShapePlotConfig]:
        upper = self.config.copy()
        lower = self.config.copy()

        upper.design_lower = False
        lower.design_upper = False

        upper.straps = False
        upper.attachment_points = False
        upper.lines = False

        lower.diagonals = False

        return upper, lower
    
    def update_scale(self):
        scale = self.selection.selected

        self.config.scale_area = None
        self.config.scale_span = None

        if scale == ScaleOptions.area:
            self.config.scale_area = self.reference_area
        elif scale == ScaleOptions.span:
            self.config.scale_span = self.reference_span
        
        self.changed.emit()
    
    def update_reference(self, reference: GliderProject):
        self.reference_area = reference.glider.shape.area
        self.reference_span = reference.glider.shape.span

        #if self.selection.selected != ScaleOptions.none:
        #    self.changed.emit()


class ShapePlotCache(Cache[GliderProject, Tuple[ShapePlot, ShapePlot, str]]):
    def get_object(self, element: str):
        project = self.elements[element]
        return ShapePlot(project.element), ShapePlot(project.element), element



class ShapeView(QtWidgets.QWidget):
    grid = False

    def __init__(self, app: GliderApp):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.app = app

        self.config = ShapeConfigWidget()
        self.layout().addWidget(self.config)

        self.config.changed.connect(self.update)

        self.plots = Canvas()
        self.plots = pyqtgraph.GraphicsLayoutWidget()
        self.plots.setBackground(None)
        self.plot_upper = Canvas()
        self.plot_lower = Canvas()


        for i, viewbox in enumerate((self.plot_upper, self.plot_lower)):
            viewbox.locked_aspect_ratio = True
            viewbox.grid = self.grid
            #viewbox.static = True
            viewbox.update_data()
            self.plots.addItem(viewbox, i, 0)
        
        self.cache = ShapePlotCache(app.state.projects)

        #self._layout.addWidget(self.buttons, 0, 1)
        #self.layout().addWidget(self.plots)
        self.layout().addWidget(self.plots)

    def update(self) -> None:
        self.plot_lower.clear()
        self.plot_upper.clear()

        selected = self.app.state.projects.get_selected()

        if selected:
            self.config.update_reference(selected)

        update = self.cache.get_update()
        config = self.config.get_config()

        for plot1, plot2, name in update.active:
            color = self.app.state.projects.elements[name].color
            dwg1 = plot1.redraw(config[0])
            dwg2 = plot2.redraw(config[1])

            self.plot_upper.addItem(LayoutGraphics(dwg1, fill=True, color=color))
            self.plot_lower.addItem(LayoutGraphics(dwg2, fill=True, color=color))
        
        self.plot_lower.update_data()
        self.plot_upper.update_data()
        self.plot_lower.autoRange()
        self.plot_upper.autoRange()
        
        self.plots.update()
