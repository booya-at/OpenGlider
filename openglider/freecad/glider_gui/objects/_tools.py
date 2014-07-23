from _base import ControlPointContainer
from PySide import QtCore, QtGui
import FreeCADGui as Gui
from pivy import coin
from pivy_primitives import Spline, reflect_x, Line
import numpy

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
        self.glider_copy = self.obj.glider_instance.copy_complete()
        self.shape = None
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
        self.form.connect(self.num_cells, QtCore.SIGNAL("valueChanged(int)"), self.update_ribs)
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

        control_points1 = [[0., 0., 0.], [1., -0.2, 0.], [2., -0.3, 0.]]
        control_points2 = [[0, -1., 0.], [1., -0.8, 0.], [2., -0.7, 0.]]
        self.cpc1 = ControlPointContainer(control_points1)
        self.cpc2 = ControlPointContainer(control_points2)
        self.spline1 = Spline(reflect_x(self.cpc1.control_point_list)[::-1] + self.cpc1.control_point_list, num=20)
        self.spline2 = Spline(reflect_x(self.cpc2.control_point_list)[::-1] + self.cpc2.control_point_list, num=20)

        self.shape = coin.SoSeparator()
        self.update_ribs()

        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.cpc1)
        self.task_separator.addChild(self.cpc2)
        self.task_separator.addChild(self.spline1.object)
        self.task_separator.addChild(self.spline2.object)

    def update_data_1(self):
        self.spline1.update(reflect_x(self.cpc1.control_point_list)[::-1] + self.cpc1.control_point_list)
        self.cpc2.control_points[-1].set_x(self.cpc1.control_points[-1].x)
        self.spline2.update(reflect_x(self.cpc2.control_point_list)[::-1] + self.cpc2.control_point_list)
        self.update_ribs()

    def update_data_2(self):
        self.spline2.update(reflect_x(self.cpc2.control_point_list)[::-1] + self.cpc2.control_point_list)
        self.cpc1.control_points[-1].set_x(self.cpc2.control_points[-1].x)
        self.spline1.update(reflect_x(self.cpc1.control_point_list)[::-1] + self.cpc1.control_point_list)
        self.update_ribs()

    def update_ribs(self):
        if self.shape is not None:
            self.shape.removeAllChildren()
            front, back = self.ribs()
            # self.shape.addChild(Line(front).object)
            # self.shape.addChild(Line(back).object)
            for i in range(len(front)):
                self.shape.addChild(Line([front[i], back[i]]).object)

    def ribs(self, faktor=0):
        mx = max([i[0] for i in self.cpc1.control_point_list])
        pos = numpy.linspace(-mx, mx, self.num_cells.value())
        front_int = self.spline1.bezier_curve.interpolate_3d(xyz=0, num=20)
        back_int = self.spline2.bezier_curve.interpolate_3d(xyz=0, num=20)
        return [map(front_int, pos), map(back_int, pos)]
