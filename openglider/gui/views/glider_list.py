from __future__ import annotations
import asyncio

import os
from typing import Any

import openglider
import qtawesome
from openglider.glider.project import GliderProject
from openglider.gui.state.glider_list import GliderListItem, GliderList
from openglider.gui.qt import QtWidgets
from openglider.gui.widgets.icon import Icon
from openglider.gui.widgets.list_select.item import ListWidgetItem, ListItemWidget
from openglider.gui.widgets.list_select.list import GenericListWidget

class GliderListWidgetItemWidget(ListItemWidget[GliderProject]):
    list_item: GliderListItem
    def __init__(self, parent: GliderListWidget, list_item: GliderListItem):
        super().__init__(parent, list_item)  # type: ignore

    
    def draw_buttons(self) -> None:
        super().draw_buttons()

        self.button_save = QtWidgets.QPushButton()
        self.button_save.setFixedSize(30, 30)
        self.button_save.setIcon(qtawesome.icon("fa.save"))
        self.button_save.clicked.connect(self.save)
        self.layout().addWidget(self.button_save)

        self.button_reload = QtWidgets.QPushButton()

    def update(self, *args: Any, **kwargs: Any) -> None:
        super().update(*args, **kwargs)

        if self.list_item.element.filename is None:
            self.button_reload.setEnabled(False)
            self.button_save.setEnabled(True)
        else:
            self.button_reload.setEnabled(True)
        
        if self.list_item.failed:
            self.setStyleSheet(f"background-color: #880000;")
        else:
            self.setStyleSheet(f"background-color: none;")

    def save(self) -> str | None:
        filters = {
            "OpenGlider ods (*.ods)": ".ods",
            "OpenGlider json (*.json)": ".json"
        }
        filename, extension = QtWidgets.QFileDialog.getSaveFileName(
            self,
            f"Save {self.list_item.element.name}",
            self.list_item.element.name,
            filter=";;".join(filters.keys())
            )

        if not filename:
            return None

        if not filename.endswith(".json") and not filename.endswith(".ods"):
            filename += filters[extension]

        self.list_item.element.save(filename)
        self.update()
        return filename

class GliderListWidgetItem(ListWidgetItem[GliderProject, GliderListWidgetItemWidget]):    
    def save(self) -> None:
        pass

    def get_widget(self, parent: GliderListWidget, element: GliderListItem) -> GliderListWidgetItemWidget:  # type: ignore
        widget = GliderListWidgetItemWidget(parent, element)

        widget.changed.connect(lambda: self._changed)
        widget.button_remove.clicked.connect(lambda: self._remove())
        widget.button_save.clicked.connect(lambda: self.save())
        #widget.button_reload.clicked.connect(lambda: self.parent)

        return widget

class GliderListWidget(GenericListWidget[GliderProject, GliderListWidgetItemWidget]):
    WidgetType = GliderListWidgetItem

    def __init__(self, parent: QtWidgets.QWidget, selection_list: GliderList):
        super().__init__(parent, selection_list)
        asyncio.create_task(selection_list.watch(self))

    @staticmethod
    def import_glider(filename: str) -> GliderProject:
        if filename.endswith(".ods"):
            glider = openglider.glider.project.GliderProject.import_ods(filename)
        else:
            glider = openglider.load(filename)

        if isinstance(glider, openglider.glider.ParametricGlider):
            project = GliderProject(glider, filename=filename)
        elif isinstance(glider, GliderProject):
            project = glider
            project.filename = filename
        else:
            raise ValueError(f"cannot import {glider}")
        
        if project.name is None:
            name = os.path.split(filename)[1]
            project.name = ".".join(name.split(".")[:-1])
        
        project.glider_3d.rename_parts()

        return project
