from __future__ import division

from pivy import coin
from PySide import QtGui, QtCore

import FreeCAD as App
import FreeCADGui as Gui

from openglider.vector.spline import Bezier

from _tools import base_tool, text_field, input_field
from pivy_primitives import Line, vector3D, ControlPointContainer


class shape_tool(base_tool):

    def __init__(self, obj):
        super(shape_tool, self).__init__(obj, widget_name="shape tool")

        # scene components
        self.shape = coin.SoSeparator()
        self.front_cpc = ControlPointContainer(vector3D(self.glider_2d.front.controlpoints), self.view)
        self.back_cpc = ControlPointContainer(vector3D(self.glider_2d.back.controlpoints), self.view)
        self.cell_dist_cpc = ControlPointContainer(vector3D(self.glider_2d.cell_dist_controlpoints), self.view)

        # form components
        self.Qnum_front = QtGui.QSpinBox(self.base_widget)
        self.Qnum_back = QtGui.QSpinBox(self.base_widget)
        self.Qnum_dist = QtGui.QSpinBox(self.base_widget)
        self.Qnum_cells = QtGui.QSpinBox(self.base_widget)
        self.Qset_const_fixed = QtGui.QCheckBox(self.base_widget)
        self.Qset_const = QtGui.QPushButton(self.base_widget)

        # add another form widget displaying data
        self.Qarea = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qarea_fixed = QtGui.QRadioButton(self.base_widget)
        self.Qaspect_ratio = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qaspect_ratio_fixed = QtGui.QRadioButton(self.base_widget)
        self.Qspan = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qspan_fixed = QtGui.QRadioButton(self.base_widget)

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
        self.cell_dist_cpc.remove_callbacks()
        super(shape_tool, self).accept()

    def reject(self):
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.cell_dist_cpc.remove_callbacks()
        super(shape_tool, self).reject()

    def setup_widget(self):
        self.Qnum_cells.setValue(int(self.glider_2d.cell_num))
        self.Qnum_front.setValue(len(self.glider_2d.front.controlpoints))
        self.Qnum_back.setValue(len(self.glider_2d.back.controlpoints))
        self.Qnum_dist.setValue(len(self.glider_2d.cell_dist_controlpoints))
        self.Qnum_cells.valueChanged.connect(self.update_num_cells)
        self.Qset_const_fixed.clicked.connect(self.auto_update_const_dist)
        self.Qset_const.clicked.connect(self.update_const)
        self.Qnum_dist.valueChanged.connect(self.update_num_dist)
        self.Qnum_back.valueChanged.connect(self.update_num_back)
        self.Qnum_front.valueChanged.connect(self.update_num_front)



        self.Qnum_cells.setMaximum(150)
        self.Qnum_back.setMaximum(5)
        self.Qnum_front.setMaximum(5)
        self.Qnum_dist.setMaximum(8)

        self.Qnum_cells.setMinimum(10)
        self.Qnum_back.setMinimum(2)
        self.Qnum_front.setMinimum(2)
        self.Qnum_dist.setMinimum(1)

        Qset_const_layout = QtGui.QHBoxLayout()
        Qset_const_layout.addWidget(self.Qset_const)
        Qset_const_layout.addWidget(self.Qset_const_fixed)

        Qspan_layout = QtGui.QHBoxLayout()
        Qspan_layout.addWidget(self.Qspan)
        Qspan_layout.addWidget(self.Qspan_fixed)

        Qarea_layout = QtGui.QHBoxLayout()
        Qarea_layout.addWidget(self.Qarea)
        Qarea_layout.addWidget(self.Qarea_fixed)

        Qaspect_ratio_layout = QtGui.QHBoxLayout()
        Qaspect_ratio_layout.addWidget(self.Qaspect_ratio)
        Qaspect_ratio_layout.addWidget(self.Qaspect_ratio_fixed)

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
        self.layout.setLayout(7, input_field, Qset_const_layout)
        self.layout.setWidget(8, text_field, QtGui.QLabel("span:"))
        self.layout.setLayout(8, input_field, Qspan_layout)

        self.layout.setWidget(9, text_field, QtGui.QLabel("flat area:"))
        self.layout.setLayout(9, input_field, Qarea_layout)
        self.layout.setWidget(10, text_field, QtGui.QLabel("aspect ratio:"))
        self.layout.setLayout(10, input_field, Qaspect_ratio_layout)

        self.update_properties()

        self.Qarea.valueChanged.connect(self.set_area)
        self.Qaspect_ratio.valueChanged.connect(self.set_aspect_ratio)
        self.Qspan.valueChanged.connect(self.set_span)

        self.Qarea_fixed.clicked.connect(self.set_fixed_property)
        self.Qspan_fixed.clicked.connect(self.set_fixed_property)
        self.Qaspect_ratio_fixed.clicked.connect(self.set_fixed_property)

        self.Qaspect_ratio_fixed.click()

    def setup_pivy(self):
        # setting on drag behavior
        self.front_cpc.on_drag.append(self.update_data_back)
        self.back_cpc.on_drag.append(self.update_data_front)
        self.cell_dist_cpc.on_drag.append(self.update_shape)

        # adding graphics to the main separator
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.front_cpc)
        self.task_separator.addChild(self.back_cpc)
        self.task_separator.addChild(self.cell_dist_cpc)
        self.update_shape()

        self.front_cpc.drag_release.append(self.update_properties)
        self.back_cpc.drag_release.append(self.update_properties)
        self.cell_dist_cpc.drag_release.append(self.update_properties)
        self.front_cpc.drag_release.append(self.auto_update_const_dist)
        self.back_cpc.drag_release.append(self.auto_update_const_dist)

    def line_edit(self):
        self.front_cpc.set_edit_mode(self.view)
        self.back_cpc.set_edit_mode(self.view)

    def rib_edit(self):
        self.cell_dist_cpc.set_edit_mode(self.view)
        self.update_shape()

    def update_properties(self):
        self.Qspan.blockSignals(True)
        self.Qarea.blockSignals(True)
        self.Qaspect_ratio.blockSignals(True)
        self.Qspan.setValue(self.glider_2d.span)
        self.Qaspect_ratio.setValue(self.glider_2d.aspect_ratio)
        self.Qarea.setValue(self.glider_2d.flat_area)
        self.Qspan.blockSignals(False)
        self.Qarea.blockSignals(False)
        self.Qaspect_ratio.blockSignals(False)

    def set_fixed_property(self):
        self.Qarea.setEnabled(True)
        self.Qspan.setEnabled(True)
        self.Qaspect_ratio.setEnabled(True)
        if self.Qarea_fixed.isChecked():
            self.Qarea.setEnabled(False)
            return "area"
        if self.Qspan_fixed.isChecked():
            self.Qspan.setEnabled(False)
            return "span"
        if self.Qaspect_ratio_fixed.isChecked():
            self.Qaspect_ratio.setEnabled(False)
            return "aspect_ratio"
        return None

    def set_area(self):
        fixed = self.set_fixed_property()
        self.glider_2d.set_flat_area(self.Qarea.value(), fixed)
        self.update_properties()
        self.front_cpc.control_pos = self.glider_2d.front.controlpoints
        self.back_cpc.control_pos = self.glider_2d.back.controlpoints
        self.cell_dist_cpc.control_pos = self.glider_2d.cell_dist.controlpoints[1:-1]
        self.update_shape()

    def set_span(self):
        fixed = self.set_fixed_property()
        self.glider_2d.set_span_1(self.Qspan.value() / 2, fixed)
        self.update_properties()
        self.front_cpc.control_pos = self.glider_2d.front.controlpoints
        self.back_cpc.control_pos = self.glider_2d.back.controlpoints
        self.cell_dist_cpc.control_pos = self.glider_2d.cell_dist.controlpoints[1:-1]
        self.update_shape()

    def set_aspect_ratio(self):
        fixed = self.set_fixed_property()
        self.glider_2d.set_aspect_ratio(self.Qaspect_ratio.value(), fixed)
        self.update_properties()
        self.front_cpc.control_pos = self.glider_2d.front.controlpoints
        self.back_cpc.control_pos = self.glider_2d.back.controlpoints
        self.cell_dist_cpc.control_pos = self.glider_2d.cell_dist.controlpoints[1:-1]
        self.update_shape()

    def update_num_dist(self, val):
        self.glider_2d.cell_dist.numpoints = val + 2
        self.cell_dist_cpc.control_pos = vector3D(self.glider_2d.cell_dist.controlpoints[1:-1])
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
        old_value = self.glider_2d.back.controlpoints[-1][0]
        new_value = self.front_cpc.control_points[-1].pos[0]
        self.back_cpc.control_points[-1].set_x(new_value)
        self.glider_2d.cell_dist._data[:, 0] *= (new_value / old_value)
        self.cell_dist_cpc.control_pos = self.glider_2d.cell_dist_controlpoints
        self.update_shape()

    def update_data_front(self):
        old_value = self.glider_2d.front.controlpoints[-1][0]
        new_value = self.back_cpc.control_points[-1].pos[0]
        self.front_cpc.control_points[-1].set_x(new_value)
        self.glider_2d.cell_dist._data[:, 0] *= (new_value / old_value)
        self.cell_dist_cpc.control_pos = self.glider_2d.cell_dist_controlpoints
        self.update_shape()

    def update_num_cells(self, val):
        self.glider_2d.cell_num = val
        self.update_shape()

    def auto_update_const_dist(self):
        if self.Qset_const_fixed.isChecked():
            self.update_const()

    def update_const(self):
        const_dist = list(self.glider_2d.depth_integrated())
        self.glider_2d.cell_dist = self.glider_2d.cell_dist.fit(
            const_dist, numpoints=self.Qnum_dist.value() + 2)
        self.cell_dist_cpc.control_pos = self.glider_2d.cell_dist_controlpoints
        self.update_shape()

    def update_shape(self, arg=None, num=30):
        self.glider_2d.front.controlpoints = [i[:-1] for i in self.front_cpc.control_pos]
        self.glider_2d.back.controlpoints = [i[:-1] for i in self.back_cpc.control_pos]
        self.glider_2d.cell_dist_controlpoints = [i[:-1] for i in self.cell_dist_cpc.control_pos]
        self.shape.removeAllChildren()
        ribs, front, back = self.glider_2d.shape(num=15).ribs_front_back
        dist_line = self.glider_2d.cell_dist_interpolation
        self.shape.addChild(Line(front, width=2).object)
        self.shape.addChild(Line(back, width=2).object)
        self.shape.addChild(Line(vector3D(self.glider_2d.front.data), color="grey").object)
        self.shape.addChild(Line(vector3D(self.glider_2d.back.data), color="grey").object)
        for rib in ribs:
            width = 1
            col = "grey"
            if list(rib) in (ribs[0], ribs[-1]):
                width = 2
                col = "black"
            self.shape.addChild(Line(rib, color=col, width=width).object)
        self.shape.addChild(Line(dist_line, color="red", width=2).object)
        for i in dist_line:
            self.shape.addChild(Line([[0, i[1]], i, [i[0], 0]], color="grey").object)

