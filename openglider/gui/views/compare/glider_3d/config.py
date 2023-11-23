from __future__ import annotations

import logging
from openglider.gui.qt import QtCore, QtWidgets

from openglider.utils.dataclass import BaseModel

logger = logging.getLogger(__name__)

class GliderViewConfig(BaseModel):
    show_panels: bool = True
    show_ribs: bool = True
    show_lines: bool = True

    show_diagonals: bool = True
    show_straps: bool = True

    show_miniribs: bool = True

    show_highres: bool = False

    profile_numpoints: int = 25
    numribs: int = 3

    def needs_recalc(self, old_config: GliderViewConfig | None=None) -> bool:
        if old_config is None:
            return True
        
        if self.show_highres:
            self.numribs = 12
            self.profile_numpoints = 120
        else:
            self.numribs = 3
            self.profile_numpoints = 25
        
        if old_config.numribs != self.numribs:
            return True
        if old_config.profile_numpoints != self.profile_numpoints:
            return True
        
        return False
    
    def get_active_keys(self) -> list[str]:
        keys = []
        if self.show_panels:
            keys.append("panels")
        if self.show_ribs:
            keys.append("ribs")
        if self.show_lines:
            keys.append("lines")
        if self.show_diagonals:
            keys.append("diagonals")
        if self.show_straps:
            keys.append("straps")
        if self.show_miniribs:
            keys.append("miniribs")
        return keys


class GliderViewConfigWidget(QtWidgets.QWidget):
    changed = QtCore.Signal()
    def __init__(self, parent: QtWidgets.QWidget, config: GliderViewConfig=None) -> None:
        super().__init__(parent)
        self.config = config or GliderViewConfig()

        self.setLayout(QtWidgets.QHBoxLayout())

        self.add_button("panels")
        self.add_button("ribs")
        self.add_button("lines")
        self.add_button("diagonals")
        self.add_button("straps")
        self.add_button("miniribs")
        self.add_button("highres")

    def add_button(self, name: str) -> None:
        checkbox = QtWidgets.QCheckBox(self)
        checkbox.setText(f"show {name}")

        def toggle() -> None:
            setattr(self.config, f"show_{name}", not getattr(self.config, f"show_{name}"))
            self.changed.emit()

        checkbox.setChecked(getattr(self.config, f"show_{name}"))
        checkbox.setText(f"show {name}")
        checkbox.clicked.connect(toggle)
        self.layout().addWidget(checkbox)
