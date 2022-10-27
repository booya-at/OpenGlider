from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, List, Tuple, TypeVar
from datetime import datetime
import re
from openglider.glider.glider import Glider
from openglider.gui.qt import QtWidgets, QtGui, QtCore
import logging

from openglider.gui.views.window import GliderWindow
from openglider.glider.project import GliderProject
from openglider.utils.colors import Color, colorwheel

if TYPE_CHECKING:
    from openglider.gui.app import GliderApp

class Wizard(GliderWindow):
    def __init__(self, app: GliderApp, project: GliderProject):
        super().__init__(app, project)

        self.logger = logging.getLogger("{}.{}".format(self.__class__.__module__, self.__class__.__name__))

        #self.project = project
    
    def get_changelog_entry(self) -> Tuple[datetime, str, str]:
        return datetime.now(), self.__class__.__name__, "Modified using wizzard"


    def apply(self, update: bool=True) -> None:
        # self.app.gliders -> [listitem, project, view]

        if update:
            self.project.update_all()

        self.project.changelog.append(self.get_changelog_entry())

        self.app.add_glider(self.project, increase_revision=True)
        self.close()


T = TypeVar("T")

class SelectionItem(QtWidgets.QWidget, Generic[T]):
    def __init__(self, obj: T, name: str):
        super().__init__()
        self.obj = obj
        self.name = name
        self.on_change = []

        self.setLayout(QtWidgets.QHBoxLayout())

        self.checkbox = QtWidgets.QCheckBox()
        self.layout().addWidget(self.checkbox)
        self.checkbox.clicked.connect(self._on_change)

        self.colorbox = QtWidgets.QGraphicsView(self)
        self.colorbox.setFixedWidth(15)
        self.colorbox.setFixedHeight(15)
        self.layout().addWidget(self.colorbox)
        self.colorbox_scene = QtWidgets.QGraphicsScene(0, 0, 10, 10)
        self.colorbox.setScene(self.colorbox_scene)

        self.label = QtWidgets.QLabel(name)
        self.layout().addWidget(self.label)
        self.layout().addStretch()

    def _on_change(self) -> None:
        for f in self.on_change:
            f(self)

    @property
    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, value: bool) -> None:
        self.checkbox.setChecked(value)

    def set_color(self, color: Color=None) -> None:
        if color is not None:
            qcolor = QtGui.QColor(*color, 255)
            brush = QtGui.QBrush(qcolor)
            self.colorbox_scene.setBackgroundBrush(brush)
        else:
            qcolor = QtGui.QColor(255, 255, 255, 0)
            brush = QtGui.QBrush(qcolor)
            self.colorbox_scene.setBackgroundBrush(brush)


class SelectionWizard(Wizard):
    project: GliderProject
    def __init__(self, app: GliderApp, project: GliderProject, selection_lst: list[Tuple[T, str]]):
        super().__init__(app, project)

        self.setLayout(QtWidgets.QHBoxLayout())

        self.main_widget = QtWidgets.QSplitter()
        self.main_widget.setOrientation(QtCore.Qt.Vertical)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.setOrientation(QtCore.Qt.Horizontal)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.splitter)


        self.right_widget = QtWidgets.QWidget()
        self.right_widget.setLayout(QtWidgets.QVBoxLayout())

        self.selection = QtWidgets.QWidget()
        self.selection.setLayout(QtWidgets.QVBoxLayout())
        self.selection.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.right_widget.layout().addWidget(self.selection)

        self.selection_items: List[SelectionItem] = []

        for obj, name in selection_lst:
            item = SelectionItem(obj, name)
            item.on_change.append(self._selection_changed)
            self.selection_items.append(item)

            self.selection.layout().addWidget(item)

        self.button_apply = QtWidgets.QPushButton("Apply")
        self.button_apply.clicked.connect(self.apply)

        self.selection.layout().addWidget(self.button_apply)

        self.splitter.addWidget(self.main_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([800, 200])

    @property
    def selected_items(self) -> List[Tuple[T, Color]]:
        # return list of gliders + colors
        lst: List[SelectionItem] = []

        for item in self.selection_items:
            if item.is_checked:
                lst.append(item)
            else:
                item.set_color()

        colors = colorwheel(len(lst))
        return_lst = []

        for i, item in enumerate(lst):
            color = colors[i]
            item.set_color(color)
            return_lst.append((item.obj, color))

        return return_lst

    def _selection_changed(self, item: Any=None) -> None:
        # todo: create color wheel & show
        self.selection_changed(self.selected_items)

    def selection_changed(self, selected: Any) -> None:
        pass


class GliderSelectionWizard(SelectionWizard):
    def __init__(self, app: GliderApp, project: GliderProject):
        selection_lst = [(project, project.name) for project in app.glider_projects]
        super().__init__(app, project, selection_lst)


