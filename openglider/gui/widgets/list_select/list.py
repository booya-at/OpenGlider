from __future__ import annotations

import logging
from typing import Any, Generic, TypeVar

from openglider.gui.state.selection_list.list import SelectionList, SelectionListItemT
from openglider.gui.qt import QtCore, QtWidgets

from .item import ListWidgetItem, ItemType, ListItemWidget

logger = logging.getLogger(__name__)

WidgetTypeT = TypeVar("WidgetTypeT", bound=ListItemWidget)


class GenericListWidget(Generic[ItemType, WidgetTypeT], QtWidgets.QListWidget):
    WidgetType: type[ListWidgetItem[ItemType, WidgetTypeT]]
    changed = QtCore.Signal()
    _has_change_handler = False

    def __init__(self, parent: QtWidgets.QWidget, selection_list: SelectionList[ItemType, SelectionListItemT]):
        super().__init__(parent=parent)
        self.selection_list = selection_list

        self.render()
    
    def render(self, *args: Any, **kwargs: Any) -> None:
        if self._has_change_handler:
            self.currentItemChanged.disconnect(self._changed)
        
        self.clear()

        for name, element in self.selection_list.items():
            if name == self.selection_list.selected_element:
                focus = True
            else:
                focus = False

            self.add(element, focus=focus)
        
        self.currentItemChanged.connect(self._changed)
        self._has_change_handler = True

    def add(self, element: SelectionListItemT, focus: bool=True) -> ListWidgetItem[ItemType, WidgetTypeT]:  # type: ignore
        list_item = self.WidgetType(self, element)
        widget = list_item.widget
        widget.changed.connect(self._changed)

        self.addItem(list_item)
        self.setItemWidget(list_item, widget)

        if focus:
            self.setCurrentItem(list_item)
        
        return list_item

    def _changed(self, current: ListWidgetItem | None=None, next_value: WidgetTypeT | None=None) -> None:
        if current is not None:
            self.selection_list.selected_element = current.item.name

        self.changed.emit()


class ListWidget(Generic[ItemType], GenericListWidget[ItemType, ListItemWidget]):
    WidgetType = ListWidgetItem