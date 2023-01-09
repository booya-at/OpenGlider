from __future__ import annotations
import logging
from typing import TypeVar, Generic, TYPE_CHECKING

from openglider.gui.state.selection_list.list import SelectionListItem, ItemType
from openglider.gui.widgets import InputLabel
from openglider.gui.widgets.icon import Icon
from openglider.utils.colors import Color
from openglider.gui.qt import QtCore, QtGui, QtWidgets

if TYPE_CHECKING:
    from .list import ListWidget
    from openglider.gui.widgets.list_select.list import GenericListWidget


logger = logging.getLogger(__name__)


class ListWidgetItemWidget(QtWidgets.QWidget, Generic[ItemType]):
    changed = QtCore.Signal()

    def __init__(self, parent: ListWidget[ItemType], list_item: SelectionListItem[ItemType]):
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
        self.list._changed()
    
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

ListItemWidgetT = TypeVar("ListItemWidgetT", bound=ListWidgetItemWidget)
 

class ListWidgetItem(QtWidgets.QListWidgetItem, Generic[ItemType, ListItemWidgetT]):
    item: SelectionListItem[ItemType]
    parent: GenericListWidget[ItemType, ListItemWidgetT]
    widget: QtWidgets.QWidget

    def __init__(self, parent: GenericListWidget[ItemType, ListItemWidgetT], element: SelectionListItem[ItemType]):
        super().__init__(parent)
        self.parent = parent
        self.item = element
        self.widget = self.get_widget(parent, element)

        self.setSizeHint(self.widget.sizeHint())
    
    def get_widget(self, parent: GenericListWidget[ItemType, ListItemWidgetT], element: SelectionListItem[ItemType]) -> ListWidgetItemWidget:
        widget = ListWidgetItemWidget(parent, element)
        widget.changed.connect(lambda: self._changed)
        widget.button_remove.clicked.connect(lambda: self._remove())

        return widget
    
    def _changed(self) -> None:
        self.parent._changed()

    def _remove(self) -> None:
        lst = self.parent.selection_list

        name = lst.get_name(self.item)
        lst.remove(name)
        self.parent.render()
        self.parent._changed()
