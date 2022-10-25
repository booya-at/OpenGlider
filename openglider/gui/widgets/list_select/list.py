from __future__ import annotations

import logging
from typing import Callable, Generic, List

from openglider.gui.app.state.list import SelectionList, SelectionListItem
from openglider.gui.qt import QtCore, QtGui, QtWidgets

from .item import ListItem, ListItemType

logger = logging.getLogger(__name__)


   

class ListWidget(QtWidgets.QListWidget, Generic[ListItemType]):
    on_change: List[Callable]
    changed = QtCore.Signal()
    _change_handler = None

    def __init__(self, parent, selection_list: SelectionList[ListItemType]):
        super().__init__(parent=parent)
        self.selection_list = selection_list

        self.on_change = []
        self.render()
    
    def render(self):
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

    def add(self, element: SelectionListItem[ListItemType], focus=True):
        list_item = ListItem(self, element)
        widget = list_item.widget
        widget.changed.connect(self._changed)

        self.addItem(list_item)
        self.setItemWidget(list_item, widget)

        if focus:
            self.setCurrentItem(list_item)

    def _changed(self, current=None, next_value=None):
        if current is None:
            current = self.currentItem()
        
        if current is not None:
            self.selection_list.selected_element = current.element.name

        self.changed.emit()
