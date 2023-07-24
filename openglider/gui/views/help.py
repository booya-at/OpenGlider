from typing import Any, Optional, Type
import PySide6.QtCore
import PySide6.QtWidgets
from openglider.gui.qt import QtWidgets

from openglider.gui.widgets.select import AutoComplete

from openglider.glider.parametric.table import GliderTables

from openglider.glider.parametric.table.base.table import ElementTable

from openglider.glider.parametric.table.base.dto import DTO

class HelpView(QtWidgets.QWidget):
    all_dtos: dict[str, DTO]

    def __init__(self, parent: QtWidgets.QWidget | None=None) -> None:
        super().__init__(parent)

        self.all_dtos = {}

        for name, _cls in GliderTables.__annotations__.items():
            if issubclass(_cls, ElementTable):
                for dto_name, dto in _cls.dtos.items():
                    self.all_dtos[dto_name] = dto

        
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        dto_names = list(self.all_dtos.keys())
        dto_names.sort()
        self.search = AutoComplete(dto_names)
        layout.addWidget(self.search)
        self.search.changed.connect(self.select)

        self.content = QtWidgets.QTextEdit()
        self.content.setReadOnly(True)
        layout.addWidget(self.content)

        self.select()

    def select(self, *args: Any, **kwargs: Any) -> None:
        dto_name = self.search.selected
        if dto_name in self.all_dtos:
            dto = self.all_dtos[dto_name]
            annotations = dto.describe()

            text = f"{dto_name}\n"
            for name, annotation in annotations:
                text += f"    - {name}: {annotation}\n"

            if dto.__doc__:
                text += dto.__doc__

            self.content.setText(text)
