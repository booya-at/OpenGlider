from typing import Type
from collections.abc import Callable
from openglider.gui.qt import QtWidgets, QtCore
import enum

import logging

from openglider.utils.dataclass import BaseModel
logger = logging.getLogger(__name__)


class ConfigWidget(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, Config: type[BaseModel], parent: QtWidgets.QWidget=None, vertical: bool=False) -> None:
        super().__init__(parent)

        if vertical:
            self.setLayout(QtWidgets.QVBoxLayout())
        else:
            self.setLayout(QtWidgets.QHBoxLayout())

        self.config = Config()
        self.checkboxes = {}

        def get_clickhandler(prop: str) -> Callable[[bool], None]:
            
            def toggle_prop(value: bool) -> None:
                setattr(self.config, prop, value)
                self.changed.emit()
            
            return toggle_prop


        for prop in self.config.__annotations__:
            checkbox = QtWidgets.QCheckBox(self)
            checkbox.setChecked(getattr(self.config, prop))
            checkbox.setText(f"{prop}")
            checkbox.clicked.connect(get_clickhandler(prop))
            self.layout().addWidget(checkbox)
            self.checkboxes[prop] = checkbox
