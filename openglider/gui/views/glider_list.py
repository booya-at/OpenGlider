import logging
import os
import sys
from typing import Callable, List

import openglider
from openglider.glider.project import GliderProject
from openglider.gui.app.state import ApplicationState
from openglider.gui.app.state.list import SelectionListItem
from openglider.gui.widgets import InputLabel
from openglider.gui.widgets.icon import Icon
from openglider.utils.colors import Color
from openglider.gui.qt import QtCore, QtGui, QtWidgets

logger = logging.getLogger(__name__)

class GliderListWidget(QtWidgets.QWidget):
    changed = QtCore.Signal()

    def __init__(self, parent: "GliderList", project: SelectionListItem[GliderProject]):
        super().__init__(parent)
        self.parent = parent
        self.project = project

        self.setLayout(QtWidgets.QHBoxLayout())

        self.button_active = QtWidgets.QPushButton()
        self.button_active.setFixedSize(30,30)
        self.update_active_icon()
        self.layout().addWidget(self.button_active)
        self.button_active.clicked.connect(self.toggle_active)

        self.button_reload = QtWidgets.QPushButton()
        self.button_reload.setIcon(Icon("elusive:refresh"))
        self.button_reload.setFixedSize(30,30)
        self.layout().addWidget(self.button_reload)

        self.button_save = QtWidgets.QPushButton()
        self.button_save.setIcon(Icon("save"))
        self.button_save.setFixedSize(30,30)
        self.button_save.clicked.connect(self.save)
        self.layout().addWidget(self.button_save)

        self.button_color = QtWidgets.QPushButton()
        self.button_color.setIcon(Icon("edit"))
        self.button_color.setFixedSize(30, 30)
        self.button_color.clicked.connect(self.choose_color)
        self.layout().addWidget(self.button_color)

        self.button_remove = QtWidgets.QPushButton()
        self.button_remove.setIcon(Icon("elusive:remove"))
        #self.button_remove.setIcon(self.style().standardIcon("edit-delete"))
        self.button_remove.setFixedSize(30, 30)
        self.layout().addWidget(self.button_remove)

        self.description_widget = QtWidgets.QWidget()
        self.description_widget.setLayout(QtWidgets.QVBoxLayout())

        self.label_name = InputLabel()
        self.label_name.on_change.append(self.update_name)
        self.description_widget.layout().addWidget(self.label_name)
        self.label_filename = QtWidgets.QLabel()
        self.description_widget.layout().addWidget(self.label_filename)
        self.label_filename.setStyleSheet("font-size: 0.6em;")
        self.label_filename.setWordWrap(True)
        self.layout().addWidget(self.description_widget)

        self.update()
    
    def toggle_active(self):
        self.project.active = not self.project.active
        self.update_active_icon()
        self.parent._changed()
    
    def update_active_icon(self):
        if self.project.active:
            self.button_active.setIcon(Icon("checked"))
            #self.button_active.setAttribute(QtCore.WA_StyledBackground, True)
            self.button_active.setStyleSheet(f"background-color: #{self.project.color.hex()};")
        else:
            self.button_active.setIcon(Icon("close"))
            self.button_active.setStyleSheet('background-color: transparent;')

    def mouseDoubleClickEvent(self, e):
        self.label_name.edit()
        print(e.button())

    def update_name(self, name):
        self.project.name = name
        self.project.element.filename = None
        self.project.element.name = name
        self.update()
    
    def choose_color(self):
        chooser = QtWidgets.QColorDialog()
        color = chooser.getColor().getRgb()
        self.project.color = Color(*color[:3])

        self.update()
        self.update_active_icon()
        self.changed.emit()

    def update(self):
        name = self.project.element.name
        if self.project.element.filename is None:
            self.button_reload.setEnabled(False)
            self.button_save.setEnabled(True)
        else:
            self.button_reload.setEnabled(True)
            #self.button_save.setEnabled(False)

        self.label_name.text = name
        self.label_filename.setText(self.project.element.filename or "-")
        self.button_color.setStyleSheet(f"background-color: #{self.project.color.hex()};")
        self.changed.emit()

    def save(self):
        filters = {
            "OpenGlider ods (*.ods)": ".ods",
            "OpenGlider json (*.json)": ".json"
        }
        filename, extension = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save {}".format(self.project.element.name),
            self.project.element.name,
            filter=";;".join(filters.keys())
            )

        if not filename:
            return

        if not filename.endswith(".json") and not filename.endswith(".ods"):
            filename += filters[extension]

        self.project.element.save(filename)
        self.update()
        return filename

    
class GliderListItem(QtWidgets.QListWidgetItem):
    project: SelectionListItem[GliderProject]

    def __init__(self, parent: "GliderList", project: SelectionListItem[GliderProject]):
        super().__init__(parent)
        self.parent = parent
        self.project = project
        self.widget = GliderListWidget(parent, project)

        self.widget.changed.connect(lambda: self._changed)
        self.widget.button_reload.clicked.connect(lambda: self._reload())
        self.widget.button_remove.clicked.connect(lambda: self._remove())

        self.setSizeHint(self.widget.sizeHint())
    
    def _changed(self):
        self.parent._changed()

    def _remove(self):
        if not self.project.element.filename:
            msgBox = QtWidgets.QMessageBox()
            
            msgBox.setText("Unsaved Glider")
            msgBox.setWindowTitle("Discard Changes?")
            #msgBox.setInformativeText(text)

            msgBox.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Save)
            ret = msgBox.exec_()

            if ret == QtWidgets.QMessageBox.Save:
                return
        
        self.parent.state.remove_glider_project(self.project.element)
        self.parent.render()
        self.parent._changed()
        
    def _reload(self):
        if self.project.element.filename:
            filename = self.project.element.filename

            project = self.parent.import_glider(filename)

            self.parent.state.update_glider_project(project)


class GliderList(QtWidgets.QListWidget):
    state: ApplicationState
    on_change: List[Callable]

    _change_handler = None

    def __init__(self, parent, state: ApplicationState):
        super().__init__(parent=parent)
        self.state = state

        self.setFont(QtGui.QFont("Sans-Serif", 15))
        self.on_change = []
        self.render()
    
    def render(self):
        if self._change_handler:
            self.currentItemChanged.disconnect(self._changed)
            self._change_handler = None
        
        self.clear()

        for name, gui_project in self.state.projects.items():
            list_item = GliderListItem(self, gui_project)
            widget = list_item.widget
            widget.changed.connect(self._changed)

            self.addItem(list_item)
            self.setItemWidget(list_item, widget)

            if name == self.state.projects.selected_element:
                self.setCurrentItem(list_item)
        
            #self._changed(None, project)

        self._change_handler = self.currentItemChanged.connect(self._changed)
    
    @staticmethod
    def import_glider(filename):
        if filename.endswith(".ods"):
            glider = openglider.glider.project.GliderProject.import_ods(filename)
        else:
            glider = openglider.load(filename)

        if isinstance(glider, openglider.glider.ParametricGlider):
            project = GliderProject(glider, filename=filename)
        elif isinstance(glider, GliderProject):
            project = glider
            project.filename = filename
        
        if project.name is None:
            name = os.path.split(filename)[1]
            project.name = ".".join(name.split(".")[:-1])
        
        project.glider_3d.rename_parts()

        return project
    
    @property
    def gliders(self):
        for i in range(self.count()):
            yield self.item(i)

    @property
    def current_glider(self):
        if not self.count():
            return
            
        item = self.currentItem()
        return item.glider

    def _changed(self, current=None, next_value=None):
        self.state.projects.reload()

        if current is None:
            current = self.currentItem()
        
        if current is not None:
            self.state.projects.selected_element = current.project.element.name

        for f in self.on_change:
            f(current)
