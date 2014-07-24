from _base import ControlPointContainer
from PySide import QtCore, QtGui
from pivy import coin
import FreeCADGui as Gui
from pivy_primitives import Line, vector3D
from openglider.glider.glider import glider_2D

text_field = QtGui.QFormLayout.LabelRole
input_field = QtGui.QFormLayout.FieldRole

class base_tool(object):
    def __init__(self, obj, widget_name="base_widget"):
        self.obj = obj
        self.obj.ViewObject.Visibility = False
        self.view = Gui.ActiveDocument.ActiveView
        self.scene = self.view.getSceneGraph()

        # form is the widget that appears in the task panel,
        self.form = QtGui.QWidget()
        self.layout = QtGui.QFormLayout(self.form)
        self.form.setWindowTitle(widget_name)

        # scene container
        self.task_separator = coin.SoSeparator()
        self.scene.addChild(self.task_separator)

    def accept(self):
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
        self.glider_copy = self.obj.glider_instance.copy_complete()
        self.glider_2d = glider_2D.import_from_glider(self.obj.glider_instance)
        self.shape = None
        self.ribs = None
        self.cpc1 = None
        self.cpc2 = None
        self.line1 = None
        self.line2 = None
        # form components
        self.manual_edit = QtGui.QPushButton("ON", self.form)
        self.num_cells = QtGui.QSpinBox(self.form)
        self.text_manual_edit = QtGui.QLabel("manual edit")
        self.text_num_cells = QtGui.QLabel("num_cells")
        #create gui

        self.setup_widget()
        self.add_pivy()

    def setup_widget(self):
        self.form.connect(self.manual_edit, QtCore.SIGNAL('clicked()'), self.line_edit)
        self.form.connect(self.num_cells, QtCore.SIGNAL("valueChanged(int)"), self.update_shape)

        self.num_cells.setValue(10)     # todo
        self.layout.setWidget(1, text_field, self.text_num_cells)
        self.layout.setWidget(1, input_field, self.num_cells)
        self.layout.setWidget(2, text_field, self.text_manual_edit)
        self.layout.setWidget(2, input_field, self.manual_edit)

    def line_edit(self):
        if self.manual_edit.text() == "ON":
            self.manual_edit.setText("OFF")
        else:
            self.manual_edit.setText("ON")
        self.cpc1.set_edit_mode(self.view, self.update_data_1)
        self.cpc2.set_edit_mode(self.view, self.update_data_2)

    def add_pivy(self):
        # set glider visibility to False
        # draw the 2d shape
        # show controlpoints

        self.cpc1 = ControlPointContainer(vector3D(self.glider_2d.front))
        self.cpc2 = ControlPointContainer(vector3D(self.glider_2d.back))
        #
        self.shape = coin.SoSeparator()
        self.update_shape()
        #
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.cpc1)
        self.task_separator.addChild(self.cpc2)

    def update_data_1(self):
        self.cpc2.control_points[0].set_x(self.cpc1.control_points[0].x)
        self.update_shape()

    def update_data_2(self):
        self.cpc1.control_points[0].set_x(self.cpc2.control_points[0].x)
        self.update_shape()

    def update_shape(self, arg=None):
        self.glider_2d.front = [i[:-1] for i in self.cpc1.control_point_list]
        self.glider_2d.back = [i[:-1] for i in self.cpc2.control_point_list]
        if arg is not None:
            self.glider_2d.cell_num = arg
        else:
            self.glider_2d.cell_num = self.num_cells.value()
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.glider_2d.discrete_front()).object)
        self.shape.addChild(Line(self.glider_2d.discrete_back()).object)
        for rib in self.glider_2d.ribs:
            self.shape.addChild(Line(rib).object)