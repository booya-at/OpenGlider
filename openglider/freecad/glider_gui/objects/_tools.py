from _base import ControlPointContainer
from PySide import QtCore, QtGui
import FreeCADGui as Gui
import FreeCAD as App
import sys
from pivy import coin
from pivy_primitives import line

class base_tool(object):
    def __init__(self, obj, widget_name="base_widget"):
        self.obj = obj
        self.obj.ViewObject.Visibility = False
        self.view = Gui.ActiveDocument.ActiveView
        self.scene = self.view.getSceneGraph()

        # form is the widget that appears in the task panel,
        # "form"... freecad convention
        self.form = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.form)
        self.form.setWindowTitle(widget_name)

        # everything that should go into the scene
        self.task_separator = coin.SoSeparator()
        self.scene.addChild(self.task_separator)

    def accept(self):
        self.obj.glider_instance.ribs[3].chord *= 1.3
        self.obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()

    def reject(self):
        self.obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()


class shape_tool(base_tool):
    def __init__(self, obj):
        super(shape_tool, self).__init__(obj, widget_name="shape-tool")
        self.cpc1 = None
        self.add_pivy()
        self.edit = QtGui.QPushButton("Edit", self.form)
        self.setup_widget()

    def setup_widget(self):
        self.form.connect(self.edit, QtCore.SIGNAL('clicked()'), self.set_edit_mode)
        self.layout.addWidget(self.edit)

    def set_edit_mode(self):
        self.cpc1.set_edit_mode(self.view, self.update_data)

    def add_pivy(self):
        # set glider visibility to False
        # draw the 2d shape
        # show controlpoints
        control_points = [[0., 0., 0.], [0.8, 0.0, 0.], [2., -0.2, 0.]]
        self.cpc1 = ControlPointContainer(control_points)
        self.line = line(self.cpc1.control_point_list)
        self.task_separator.addChild(self.cpc1)
        self.task_separator.addChild(self.line.object)

    def update_data(self):
        self.line.update(self.cpc1.control_point_list)
