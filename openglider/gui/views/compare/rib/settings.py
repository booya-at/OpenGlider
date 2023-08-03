import logging
from collections.abc import Callable

from openglider.glider.project import GliderProject
from openglider.gui.qt import QtCore, QtWidgets
from openglider.gui.widgets.flow_layout import FlowLayout
from openglider.gui.widgets.slider import Slider
from openglider.utils.dataclass import BaseModel
from pydantic import Field

logger = logging.getLogger(__name__)


class RibPlotLayers(BaseModel):
    crossports: bool=True
    rigidfoils: bool=True
    sewing: bool=True

    laser: bool=False
    text: bool=False
    marks: bool=False
    outline: bool=False

class RibPlotConfig(BaseModel):
    layers: RibPlotLayers=Field(default_factory=RibPlotLayers)
    rib_no: int=0


class RibCompareSettings(QtWidgets.QWidget):
    changed = QtCore.Signal()
    def __init__(self, parent: QtWidgets.QWidget=None) -> None:
        super().__init__(parent)
        self.config = RibPlotConfig()

        self.setLayout(FlowLayout())

        self.slider = Slider(self, "Rib")
        self.layout().addWidget(self.slider)
        self.slider.on_change(self.set_rib)
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
        
    def set_rib(self, rib_no: int) -> None:
        self.config.rib_no = rib_no
        self.changed.emit()
    
    def update_reference(self, reference: GliderProject) -> None:
        self.slider.set_bounds(0, len(reference.glider_3d.ribs)-1)





