from __future__ import annotations

import logging
from typing import Generic, Type, TypeVar

from openglider.gui.state.selection_list.list import SelectionList, SelectionListItemT
from openglider.gui.qt import QtCore, QtWidgets

from .item import ListWidgetItem, ItemType

logger = logging.getLogger(__name__)

WidgetTypeT = TypeVar("WidgetTypeT", bound=ListWidgetItem)


class GenericListWidget(Generic[ItemType, WidgetTypeT], QtWidgets.QListWidget):
    WidgetType: Type[WidgetTypeT]
    changed = QtCore.Signal()
    _change_handler = None

    def __init__(self, parent: QtWidgets.QWidget, selection_list: SelectionList[ItemType, SelectionListItemT]):
        super().__init__(parent=parent)
        self.selection_list = selection_list

        self.render()
    
    def render(self) -> None:
        if self._change_handler:
            self.currentItemChanged.disconnect(self._changed)
            self._change_handler = None
        
        self.clear()

        for name, element in self.selection_list.items():
            if name == self.selection_list.selected_element:
                focus = True
            else:
                focus = False

            self.add(element, focus=focus)

        self._change_handler = self.currentItemChanged.connect(self._changed)

    def add(self, element: SelectionListItemT, focus: bool=True) -> WidgetTypeT:  # type: ignore
        list_item = self.WidgetType(self, element)
        widget = list_item.widget
        widget.changed.connect(self._changed)

        self.addItem(list_item)
        self.setItemWidget(list_item, widget)

        if focus:
            self.setCurrentItem(list_item)
        
        return list_item

    def _changed(self, current: WidgetTypeT | None=None, next_value: WidgetTypeT | None=None) -> None:
        if current is not None:
            self.selection_list.selected_element = current.item.name

        self.changed.emit()


class ListWidget(Generic[ItemType], GenericListWidget[ItemType, ListWidgetItem]):
    WidgetType = ListWidgetItem