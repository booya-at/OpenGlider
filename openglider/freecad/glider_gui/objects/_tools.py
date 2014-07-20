from _base import ControlPointContainer
from PySide import QtCore, QtGui
import FreeCADGui as Gui
import FreeCAD as App
import sys

class base_tool(object):
    def __init__(self, obj, widget_name="base_widget"):
        self.obj = obj
        self.view = Gui.ActiveDocument.ActiveView
        self.scene = self.view.getSceneGraph()
        self.form = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout(self.form)
        self.form.setWindowTitle(widget_name)


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
        self.cpc1.set_edit_mode(self.view)

    def add_pivy(self):
        # set glider visibility to False
        # draw the 2d shape
        # show controlpoints
        control_points = [[0., 1., 0.], [1., 0.8, 0.], [2., 0.5, 0.]]
        self.cpc1 = ControlPointContainer(control_points)
        self.scene.addChild(self.cpc1)
        # cpc.set_edit_mode(self.view)
        # App.ActiveDocument.recompute()