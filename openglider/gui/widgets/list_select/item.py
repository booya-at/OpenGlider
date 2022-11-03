from __future__ import annotations
import logging
from typing import TypeVar, Generic, TYPE_CHECKING

from openglider.gui.app.state.list import SelectionListItem
from openglider.gui.widgets import InputLabel
from openglider.gui.widgets.icon import Icon
from openglider.utils.colors import Color
from openglider.gui.qt import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from .list import ListWidget


logger = logging.getLogger(__name__)

ListItemType = TypeVar("ListItemType")


class ListItemWidget(QtWidgets.QWidget, Generic[ListItemType]):
    changed = QtCore.Signal()

    def __init__(self, parent: ListWidget[ListItemType], list_item: SelectionListItem[ListItemType]):
        super().__init__(parent)
        self.list = parent
        self.list_item = list_item

        self.setLayout(QtWidgets.QHBoxLayout())

        self.draw_buttons()



        self.description_widget = QtWidgets.QWidget()
        self.description_widget.setLayout(QtWidgets.QVBoxLayout())

        self.label_name = InputLabel()
        self.label_name.text = self.list_item.name
        self.label_name.on_change.append(self.update_name)
        self.description_widget.layout().addWidget(self.label_name)
        self.layout().addWidget(self.description_widget)

        self.update()

    def draw_buttons(self) -> None:
        self.button_active = QtWidgets.QPushButton()
        self.button_active.setFixedSize(30,30)
        self.update_active_icon()
        self.layout().addWidget(self.button_active)
        self.button_active.clicked.connect(self.toggle_active)

        self.button_color = QtWidgets.QPushButton()
        self.button_color.setIcon(Icon("edit"))
        self.button_color.setFixedSize(30, 30)
        self.button_color.clicked.connect(self.choose_color)
        self.layout().addWidget(self.button_color)

        self.button_remove = QtWidgets.QPushButton()
        self.button_remove.setIcon(Icon("trash"))
        self.button_remove.setFixedSize(30, 30)
        self.layout().addWidget(self.button_remove)

    
    def toggle_active(self) -> None:
        self.list_item.active = not self.list_item.active
        self.update_active_icon()
        self.parent._changed()
    
    def update_active_icon(self) -> None:
        if self.list_item.active:
            self.button_active.setIcon(Icon("checked"))
            #self.button_active.setAttribute(QtCore.WA_StyledBackground, True)
            self.button_active.setStyleSheet(f"background-color: #{self.list_item.color.hex()};")
        else:
            self.button_active.setIcon(Icon("close"))
            self.button_active.setStyleSheet('background-color: transparent;')

    def mouseDoubleClickEvent(self, e: QtGui.QMouseEvent) -> None:
        self.label_name.edit()
        print(e.button())

    def update_name(self, name: str) -> None:
        self.list_item.name = name

        lst = self.list.selection_list
        lst.reload()
        self.update()
    
    def choose_color(self) -> None:
        chooser = QtWidgets.QColorDialog()
        color = chooser.getColor().getRgb()
        self.list_item.color = Color(*color[:3])

        self.update()
        self.update_active_icon()
        self.changed.emit()

    def update(self) -> None:
        self.button_color.setStyleSheet(f"background-color: #{self.list_item.color.hex()};")

 
class ListItem(QtWidgets.QListWidgetItem, Generic[ListItemType]):
    project: SelectionListItem[ListItemType]

    def __init__(self, parent: ListWidget[ListItemType], element: SelectionListItem[ListItemType]):
        super().__init__(parent)
        self.parent = parent
        self.element = element
        self.widget = ListItemWidget(parent, element)

        self.widget.changed.connect(lambda: self._changed)
        self.widget.button_remove.clicked.connect(lambda: self._remove())

        self.setSizeHint(self.widget.sizeHint())
    
    def _changed(self) -> None:
        self.parent._changed()

    def _remove(self) -> None:
        lst = self.parent.selection_list

        name = lst.get_name(self.element)
        lst.remove(name)
        self.parent.render()
        self.parent._changed()
