from __future__ import division

import time
import numpy as np

from pivy import coin
from pivy.graphics import Line as _Line

import FreeCAD as App
import FreeCADGui as Gui
from openglider.vector.polygon import CirclePart
from openglider.vector import PolyLine2D
from openglider.vector.spline import Bezier
from PySide import QtCore, QtGui

from .tools import (
    BaseTool,
    input_field,
    text_field,
    ControlPointContainer,
    vector2D,
    vector3D,
    Line_old,
)


class ShapeTool(BaseTool):
    widget_name = "Shape Tool"

    def __init__(self, obj):
        super(ShapeTool, self).__init__(obj)

        # scene components
        self.shape = coin.SoSeparator()
        points = list(
            map(vector3D, self.parametric_glider.shape.front_curve.controlpoints)
        )
        self.front_cpc = ControlPointContainer(self.rm, points)
        points = list(
            map(vector3D, self.parametric_glider.shape.back_curve.controlpoints)
        )
        self.back_cpc = ControlPointContainer(self.rm, points)
        points = list(
            map(vector3D, self.parametric_glider.shape.rib_dist_controlpoints)
        )
        self.cell_dist_cpc = ControlPointContainer(self.rm, points)

        # form components
        self.Qnum_front = QtGui.QSpinBox(self.base_widget)
        self.Qnum_back = QtGui.QSpinBox(self.base_widget)
        self.Qnum_dist = QtGui.QSpinBox(self.base_widget)
        self.Qnum_cells = QtGui.QSpinBox(self.base_widget)
        self.Qset_const_fixed = QtGui.QCheckBox(self.base_widget)
        self.Qset_const = QtGui.QPushButton(self.base_widget)
        # self.Qset_zero = QtGui.QPushButton('set zero', self.base_widget)

        # add another form widget displaying data
        self.Qarea = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qarea_fixed = QtGui.QRadioButton(self.base_widget)
        self.Qaspect_ratio = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qaspect_ratio_fixed = QtGui.QRadioButton(self.base_widget)
        self.Qspan = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qspan_fixed = QtGui.QRadioButton(self.base_widget)

        self.circle_front = coin.SoSeparator()
        self.circle_back = coin.SoSeparator()
        self.center_line = coin.SoSeparator()
        self.rib_lengths = coin.SoSeparator()

        self.setup_widget()
        self.setup_pivy()
        Gui.SendMsgToActiveView("ViewFit")

    def accept(self):
        self.parametric_glider.rescale_curves()
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.cell_dist_cpc.remove_callbacks()
        super(ShapeTool, self).accept()
        self.update_view_glider()

    def reject(self):
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.cell_dist_cpc.remove_callbacks()
        super(ShapeTool, self).reject()

    def update_controls(self):
        self.front_cpc.control_pos = (
            self.parametric_glider.shape.front_curve.controlpoints
        )
        self.back_cpc.control_pos = (
            self.parametric_glider.shape.back_curve.controlpoints
        )
        self.cell_dist_cpc.control_pos = (
            self.parametric_glider.shape.rib_distribution.controlpoints[1:-1]
        )

    def setup_widget(self):
        self.Qnum_cells.setValue(int(self.parametric_glider.shape.cell_num))
        self.Qnum_front.setValue(
            len(self.parametric_glider.shape.front_curve.controlpoints)
        )
        self.Qnum_back.setValue(
            len(self.parametric_glider.shape.back_curve.controlpoints)
        )
        self.Qnum_dist.setValue(
            len(self.parametric_glider.shape.rib_dist_controlpoints)
        )
        self.Qnum_cells.valueChanged.connect(self.update_num_cells)
        self.Qset_const_fixed.clicked.connect(self.auto_update_const_dist)
        self.Qset_const.clicked.connect(self.update_const)
        self.Qnum_dist.valueChanged.connect(self.update_num_dist)
        self.Qnum_back.valueChanged.connect(self.update_num_back)
        self.Qnum_front.valueChanged.connect(self.update_num_front)

        self.Qnum_cells.setMaximum(150)
        self.Qnum_back.setMaximum(9)
        self.Qnum_front.setMaximum(9)
        self.Qnum_dist.setMaximum(9)

        self.Qnum_cells.setMinimum(3)
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

        # self.layout.setWidget(1, text_field, QtGui.QLabel('manual shape edit'))
        # self.layout.setWidget(1, input_field, self.Qmanual_edit)
        self.layout.setWidget(2, text_field, QtGui.QLabel("front num_points"))
        self.layout.setWidget(2, input_field, self.Qnum_front)
        self.layout.setWidget(3, text_field, QtGui.QLabel("back num_points"))
        self.layout.setWidget(3, input_field, self.Qnum_back)
        # self.layout.setWidget(4, text_field, QtGui.QLabel('manual cell pos'))
        # self.layout.setWidget(4, input_field, self.Qcheck1)
        self.layout.setWidget(4, text_field, QtGui.QLabel("num_cells"))
        self.layout.setWidget(4, input_field, self.Qnum_cells)
        self.layout.setWidget(5, text_field, QtGui.QLabel("dist num_points"))
        self.layout.setWidget(5, input_field, self.Qnum_dist)
        self.layout.setWidget(6, text_field, QtGui.QLabel("constant AR"))
        self.layout.setLayout(6, input_field, Qset_const_layout)
        # self.layout.setWidget(7, input_field, self.Qset_zero)
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

        def update_shape_preview(*arg):
            self.update_shape(True)

        self.cell_dist_cpc.on_drag.append(update_shape_preview)

        # adding graphics to the main separator
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.front_cpc)
        self.task_separator.addChild(self.back_cpc)
        self.task_separator.addChild(self.cell_dist_cpc)
        self.task_separator.addChild(self.circle_front)
        self.task_separator.addChild(self.circle_back)
        self.task_separator.addChild(self.center_line)
        self.task_separator.addChild(self.rib_lengths)

        # set drag_release callbacks
        self.front_cpc.on_drag += [self.update_shape]
        self.front_cpc.on_drag += [self.update_properties]
        self.front_cpc.drag_release += [self.auto_update_const_dist, self.draw_lenghts]

        self.back_cpc.on_drag += [self.update_shape]
        self.back_cpc.on_drag += [self.update_properties]
        self.back_cpc.drag_release += [self.auto_update_const_dist, self.draw_lenghts]

        self.cell_dist_cpc.on_drag += [self.update_properties]
        self.cell_dist_cpc.on_drag += [self.update_shape]
        self.cell_dist_cpc.on_drag_release += [self.draw_lenghts]

        self.update_shape()
        self.draw_lenghts()

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
        self.Qspan.setValue(self.parametric_glider.shape.span)
        self.Qaspect_ratio.setValue(self.parametric_glider.shape.aspect_ratio)
        self.Qarea.setValue(self.parametric_glider.shape.area)
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
        self.parametric_glider.shape.set_area(self.Qarea.value(), fixed)
        self.update_properties()
        self.update_controls()
        self.update_shape()

    def set_span(self):
        fixed = self.set_fixed_property()
        self.parametric_glider.shape.set_span(self.Qspan.value(), fixed)
        self.update_properties()
        self.update_controls()
        self.update_shape()

    def set_aspect_ratio(self):
        fixed = self.set_fixed_property()
        self.parametric_glider.shape.set_aspect_ratio(self.Qaspect_ratio.value(), fixed)
        self.update_properties()
        self.update_controls()
        self.update_shape()

    def update_num_dist(self, val):
        self.parametric_glider.shape.rib_distribution.numpoints = val + 2
        self.cell_dist_cpc.control_pos = list(
            map(
                vector3D,
                self.parametric_glider.shape.rib_distribution.controlpoints[1:-1],
            )
        )
        self.update_shape()

    def update_num_front(self, val):
        self.parametric_glider.shape.front_curve.numpoints = val
        self.front_cpc.control_pos = list(
            map(vector3D, self.parametric_glider.shape.front_curve.controlpoints)
        )
        self.update_shape()

    def update_num_back(self, val):
        self.parametric_glider.shape.back_curve.numpoints = val
        self.back_cpc.control_pos = list(
            map(vector3D, self.parametric_glider.shape.back_curve.controlpoints)
        )
        self.update_shape()

    def update_data_back(self):
        if self.front_cpc.control_points[-1] in self.front_cpc.interaction.drag_objects:
            old_value = self.parametric_glider.shape.back_curve.controlpoints[-1][0]
            new_value = self.front_cpc.control_points[-1].points[0][0]
            p = self.back_cpc.control_points[-1].points
            p[0][0] = new_value
            self.back_cpc.control_points[-1].points = p
            self.parametric_glider.shape.rib_distribution._data[:, 0] *= (
                new_value / old_value
            )
            self.cell_dist_cpc.control_pos = (
                self.parametric_glider.shape.rib_dist_controlpoints
            )
        self.update_shape(preview=True)

    def update_data_front(self):
        if self.back_cpc.control_points[-1] in self.back_cpc.interaction.drag_objects:
            old_value = self.parametric_glider.shape.front_curve.controlpoints[-1][0]
            new_value = self.back_cpc.control_points[-1].points[0][0]
            p = self.front_cpc.control_points[-1].points
            p[0][0] = new_value
            self.front_cpc.control_points[-1].points = p
            self.parametric_glider.shape.rib_distribution._data[:, 0] *= (
                new_value / old_value
            )
            self.cell_dist_cpc.control_pos = (
                self.parametric_glider.shape.rib_dist_controlpoints
            )
        self.update_shape(preview=True)

    def update_num_cells(self, val):
        self.parametric_glider.shape.cell_num = val
        self.update_shape()
        self.draw_lenghts()

    def auto_update_const_dist(self):
        if self.Qset_const_fixed.isChecked():
            self.update_const()

    def update_const(self):
        self.parametric_glider.shape.set_const_cell_dist()
        self.cell_dist_cpc.control_pos = (
            self.parametric_glider.shape.rib_dist_controlpoints
        )
        self.update_shape()
        self.draw_lenghts()

    def draw_lenghts(self):
        self.rib_lengths.removeAllChildren()
        _shape = self.parametric_glider.shape.get_half_shape()
        scale_factor = _shape.ribs[-1][0][0] / len(_shape.ribs) * 0.01
        rot = coin.SoRotationXYZ()
        rot.axis = coin.SoRotationXYZ.Z
        rot.angle.setValue(np.pi / 2)
        color = coin.SoMaterial()
        color.diffuseColor = [0, 0, 0]
        for i, rib in enumerate(_shape.ribs):
            l = rib[0][1] - rib[1][1]
            scale = coin.SoScale()
            scale.scaleFactor = [scale_factor * l] * 3  # use total span
            front = np.array(rib[0] + [0])
            back = np.array(rib[1] + [0])
            f = 1.0
            pos = back * f + front * (1 - f)
            pos[0] = -pos[0]
            trans = coin.SoTranslation()
            trans.translation = pos
            textsep = coin.SoSeparator()
            text = coin.SoAsciiText()
            text.string = "rib_{}, l = {} m, x = {}, y = {}".format(
                i, round(l, 2), round(front[0], 2), round(front[1], 2)
            )
            textsep += [color, trans, scale, rot, text]
            self.rib_lengths += textsep

    def text_repr(self, value):
        return str(round(value, 4))

    def update_shape(self, preview=False):
        self.parametric_glider.shape.front_curve.controlpoints = list(
            map(vector2D, self.front_cpc.control_pos)
        )
        self.parametric_glider.shape.back_curve.controlpoints = list(
            map(vector2D, self.back_cpc.control_pos)
        )
        self.parametric_glider.shape.rib_dist_controlpoints = list(
            map(vector2D, self.cell_dist_cpc.control_pos)
        )
        self.shape.removeAllChildren()
        self.rib_lengths.removeAllChildren()
        mirrored_sep = coin.SoSeparator()
        sep = coin.SoSeparator()
        self.shape += mirrored_sep, sep
        mirror = coin.SoMatrixTransform()
        mirror.matrix.setValue(-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        mirrored_sep += mirror, sep
        _shape = self.parametric_glider.shape.get_half_shape()
        ribs = _shape.ribs
        front = _shape.front
        back = _shape.back
        front[0, 0] = 0
        back[0, 0] = 0
        dist_line = self.parametric_glider.shape.fast_interpolation
        sep += Line_old(front, width=2).object
        sep += Line_old(back, width=2).object
        # sep += (Line_old([back.data[0], front.data[0]], width=2).object)
        sep += Line_old([back.data[-1], front.data[-1]], width=2).object

        points = list(map(vector3D, self.parametric_glider.shape.front_curve.data))
        sep += Line_old(points, color="grey").object
        points = list(map(vector3D, self.parametric_glider.shape.back_curve.data))
        sep += Line_old(points, color="grey").object
        self.shape += Line_old(dist_line, color="red", width=2).object

        # draw circles
        self.circle_front.removeAllChildren()
        self.circle_back.removeAllChildren()
        circle_front = CirclePart(
            *self.parametric_glider.shape.front_curve.get_sequence()[[0, 10, -1]]
        )
        circle_back = CirclePart(
            *self.parametric_glider.shape.back_curve.get_sequence()[[0, 10, -1]]
        )
        self.circle_front.addChild(
            Line_old(circle_front.get_sequence(), color="red").object
        )
        self.circle_back.addChild(
            Line_old(circle_back.get_sequence(), color="red").object
        )

        # draw center line
        self.center_line.removeAllChildren()
        center_line = []
        for rib_no in range(_shape.rib_no):
            center_line.append(_shape.get_point(rib_no, 0.5))
        self.center_line.addChild(Line_old(center_line, color="red").object)
        y = _shape.get_point(0, 0.5)[1]
        x = _shape.get_point(_shape.rib_no - 1, 0)[0] * 1.2
        center_line2 = PolyLine2D([[-x, y], [x, y]])
        self.center_line.addChild(Line_old(center_line2, color="red").object)

        if not preview:
            for rib in ribs:
                width = 1
                col = "grey"
                if list(rib) in (ribs[0], ribs[-1]):
                    width = 2
                    col = "black"
                sep += Line_old(rib, color=col, width=width).object
            for i in dist_line:
                sep += Line_old([[0, i[1]], i, [i[0], 0]], color="grey").object
