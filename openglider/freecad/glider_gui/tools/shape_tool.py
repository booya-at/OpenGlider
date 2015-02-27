from pivy import coin
from PySide import QtGui, QtCore

import FreeCAD as App
import FreeCADGui as Gui

from openglider.vector.spline import BezierCurve

from _tools import base_tool, text_field, input_field
from pivy_primitives import Line, vector3D, ControlPointContainer


class shape_tool(base_tool):

    def __init__(self, obj):
        super(shape_tool, self).__init__(obj, widget_name="shape tool")

        # scene components
        self.shape = coin.SoSeparator()
        self.front_cpc = ControlPointContainer(vector3D(self.glider_2d.front.controlpoints), self.view)
        self.back_cpc = ControlPointContainer(vector3D(self.glider_2d.back.controlpoints), self.view)
        self.rib_pos_cpc = ControlPointContainer(vector3D(self.glider_2d.cell_dist_controlpoints), self.view)

        # form components
        # self.Qmanual_edit = QtGui.QCheckBox(self.base_widget)
        self.Qnum_front = QtGui.QSpinBox(self.base_widget)
        self.Qnum_back = QtGui.QSpinBox(self.base_widget)
        self.Qnum_dist = QtGui.QSpinBox(self.base_widget)
        self.Qnum_cells = QtGui.QSpinBox(self.base_widget)
        # self.Qcheck1 = QtGui.QCheckBox(self.base_widget)
        self.Qset_const = QtGui.QPushButton(self.base_widget)

        self.setup_widget()
        self.setup_pivy()
        Gui.SendMsgToActiveView("ViewFit")

    def accept(self):
        try:
            self.glider_2d.get_glider_3d(self.obj.glider_instance)
        except Exception as e:
            App.Console.PrintError(e)
            self.glider_2d.get_glider_3d(self.obj.glider_instance)
            return
        self.obj.glider_2d = self.glider_2d
        self.obj.ViewObject.Proxy.updateData()
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.rib_pos_cpc.remove_callbacks()
        super(shape_tool, self).accept()

    def reject(self):
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.rib_pos_cpc.remove_callbacks()
        super(shape_tool, self).reject()

    def setup_widget(self):
        self.Qnum_cells.setValue(int(self.glider_2d.cell_num))
        self.Qnum_front.setValue(len(self.glider_2d.front.controlpoints))
        self.Qnum_back.setValue(len(self.glider_2d.back.controlpoints))
        self.Qnum_dist.setValue(len(self.glider_2d.cell_dist_controlpoints))
        # self.base_widget.connect(self.Qmanual_edit, QtCore.SIGNAL('stateChanged(int)'), self.line_edit)
        # self.base_widget.connect(self.Qcheck1, QtCore.SIGNAL('stateChanged(int)'), self.rib_edit)
        self.base_widget.connect(self.Qnum_cells, QtCore.SIGNAL('valueChanged(int)'), self.update_num_cells)
        self.base_widget.connect(self.Qset_const, QtCore.SIGNAL('clicked()'), self.update_const)
        self.base_widget.connect(self.Qnum_dist, QtCore.SIGNAL('valueChanged(int)'), self.update_num_dist)
        self.base_widget.connect(self.Qnum_back, QtCore.SIGNAL('valueChanged(int)'), self.update_num_back)
        self.base_widget.connect(self.Qnum_front, QtCore.SIGNAL('valueChanged(int)'), self.update_num_front)

        self.Qnum_cells.setMaximum(150)
        self.Qnum_back.setMaximum(5)
        self.Qnum_front.setMaximum(5)
        self.Qnum_dist.setMaximum(5)

        self.Qnum_cells.setMinimum(10)
        self.Qnum_back.setMinimum(2)
        self.Qnum_front.setMinimum(2)
        self.Qnum_dist.setMinimum(1)

        # self.layout.setWidget(1, text_field, QtGui.QLabel("manual shape edit"))
        # self.layout.setWidget(1, input_field, self.Qmanual_edit)
        self.layout.setWidget(2, text_field, QtGui.QLabel("front num_points"))
        self.layout.setWidget(2, input_field, self.Qnum_front)
        self.layout.setWidget(3, text_field, QtGui.QLabel("back num_points"))
        self.layout.setWidget(3, input_field, self.Qnum_back)
        # self.layout.setWidget(4, text_field, QtGui.QLabel("manual cell pos"))
        # self.layout.setWidget(4, input_field, self.Qcheck1)
        self.layout.setWidget(5, text_field, QtGui.QLabel("num_cells"))
        self.layout.setWidget(5, input_field, self.Qnum_cells)
        self.layout.setWidget(6, text_field, QtGui.QLabel("dist num_points"))
        self.layout.setWidget(6, input_field, self.Qnum_dist)
        self.layout.setWidget(7, text_field, QtGui.QLabel("constant AR"))
        self.layout.setWidget(7, input_field, self.Qset_const)

    def setup_pivy(self):
        # setting on drag behavior
        self.front_cpc.on_drag.append(self.update_data_back)
        self.back_cpc.on_drag.append(self.update_data_front)
        self.rib_pos_cpc.on_drag.append(self.update_shape)

        # adding graphics to the main separator
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.front_cpc)
        self.task_separator.addChild(self.back_cpc)
        self.task_separator.addChild(self.rib_pos_cpc)
        self.update_shape()

    def line_edit(self):
        self.front_cpc.set_edit_mode(self.view)
        self.back_cpc.set_edit_mode(self.view)

    def rib_edit(self):
        self.rib_pos_cpc.set_edit_mode(self.view)
        self.update_shape()

    def update_num_dist(self, val):
        self.glider_2d.cell_dist.numpoints = val + 2
        self.rib_pos_cpc.control_pos = vector3D(self.glider_2d.cell_dist.controlpoints[1:-1])
        self.update_shape()

    def update_num_front(self, val):
        self.glider_2d.front.numpoints = val
        self.front_cpc.control_pos = vector3D(self.glider_2d.front.controlpoints)
        self.update_shape()

    def update_num_back(self, val):
        self.glider_2d.back.numpoints = val
        self.back_cpc.control_pos = vector3D(self.glider_2d.back.controlpoints)
        self.update_shape()

    def update_data_back(self):
        self.back_cpc.control_points[-1].set_x(self.front_cpc.control_points[-1].pos[0])
        self.update_shape()

    def update_data_front(self):
        self.front_cpc.control_points[-1].set_x(self.back_cpc.control_points[-1].pos[0])
        self.update_shape()

    def update_num_cells(self, val):
        self.glider_2d.cell_num = val
        self.update_shape()

    def update_const(self):
        const_dist = list(self.glider_2d.depth_integrated())
        self.glider_2d.cell_dist = BezierCurve.fit(const_dist, numpoints=self.Qnum_dist.value() + 2)
        self.rib_pos_cpc.control_pos = self.glider_2d.cell_dist_controlpoints
        self.update_shape()

    def update_shape(self, arg=None, num=30):
        self.glider_2d.front.controlpoints = [i[:-1] for i in self.front_cpc.control_pos]
        self.glider_2d.back.controlpoints = [i[:-1] for i in self.back_cpc.control_pos]
        self.glider_2d.cell_dist_controlpoints = [i[:-1] for i in self.rib_pos_cpc.control_pos]
        self.shape.removeAllChildren()
        ribs, front, back = self.glider_2d.shape(num=15)
        dist_line = self.glider_2d.cell_dist_interpolation
        self.shape.addChild(Line(front).object)
        self.shape.addChild(Line(back).object)
        for rib in ribs:
            self.shape.addChild(Line(rib).object)
        self.shape.addChild(Line(dist_line).object)
        for i in dist_line:
            self.shape.addChild(Line([[0, i[1]], i, [i[0], 0]], color="gray").object)
