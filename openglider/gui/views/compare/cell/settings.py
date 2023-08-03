import logging
from collections.abc import Callable

from openglider.glider.project import GliderProject
from openglider.gui.qt import QtCore, QtWidgets
from openglider.gui.widgets.flow_layout import FlowLayout
from openglider.gui.widgets.slider import Slider
from openglider.utils.dataclass import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


class CellPlotLayers(BaseModel):
    entry: bool = True
    ballooning: bool = True


class CellPlotConfig(BaseModel):
    layers: CellPlotLayers = Field(default_factory=CellPlotLayers)
    cell_no: int=0


class CellCompareSettings(QtWidgets.QWidget):
    changed = QtCore.Signal()
    
    def __init__(self, parent: QtWidgets.QWidget=None) -> None:
        super().__init__(parent)
        self.config = CellPlotConfig()

        self.setLayout(FlowLayout())

        self.slider = Slider(self, "Cell")
        self.layout().addWidget(self.slider)
        self.slider.on_change(self.set_cell)
        self.slider.setMinimumWidth(500)

        self.checkboxes = {}

        def get_clickhandler(layer_name: str) -> Callable[[bool], None]:
            
            def toggle_layer(value: bool) -> None:
                setattr(self.config.layers, layer_name, value)
                self.changed.emit()
            
            return toggle_layer

        for layer_name in self.config.layers.__annotations__:

            checkbox = QtWidgets.QCheckBox(self)
            checkbox.setChecked(getattr(self.config.layers, layer_name))
            checkbox.setText(f"show {layer_name}")
            checkbox.clicked.connect(get_clickhandler(layer_name))
            self.layout().addWidget(checkbox)
            self.checkboxes[layer_name] = checkbox
        
    def set_cell(self, cell_no: int) -> None:
        self.config.cell_no = cell_no
        self.changed.emit()
    
    def update_reference(self, reference: GliderProject) -> None:
        self.slider.set_bounds(0, len(reference.glider_3d.cells)-1)





