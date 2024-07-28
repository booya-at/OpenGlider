# -*- coding: utf-8 -*-
from __future__ import division

import numpy as np
from pivy import coin

from openglider.glider.rib import Rib
from PySide import QtGui

from pivy import graphics
from .tools import (
    BaseTool,
    input_field,
    spline_select,
    text_field,
    ControlPointContainer,
    Line_old,
    vector3D,
)


class SpanMappingTool(BaseTool):
    num_on_drag = 80
    num_release = 200
    widget_name = "span mapping"
    scale = np.array([1.0, 1.0])
    grid_y_diff = 1.0
    value_scale = 1.0

    def __init__(self, obj):
        super(SpanMappingTool, self).__init__(obj)
        self._grid_y_diff = self.grid_y_diff / self.value_scale
        pts = np.array(self.spline.controlpoints) * self.scale
        pts = list(map(vector3D, pts))

        self.spline_controlpoints = ControlPointContainer(self.rm, pts)
        self.spline_curve = Line_old([], color="red", width=2)

        self.shape = coin.SoSeparator()
        self.coords = coin.SoSeparator()
        self.grid = coin.SoSeparator()

        self.ribs = self.parametric_glider.shape.ribs
        self.front = [rib[0] for rib in self.ribs]
        self.back = [rib[1] for rib in self.ribs]
        self.text_scale = self.parametric_glider.shape.span / len(self.front) / 20.0
        self.x_grid = [i[0] for i in self.front]

        self.Qnum_aoa = QtGui.QSpinBox(self.base_widget)
        self.spline_select = spline_select(
            [self.spline], self.update_spline_type, self.base_widget
        )

        self.setup_widget()
        self.setup_pivy()
        self.update_num()

    @property
    def spline(self):
        """
        overwrite this function!!!
        """
        return self.parametric_glider.zrot

    def setup_pivy(self):
        # fix last node (span)
        self.spline_controlpoints.control_points[-1].constrained = [0.0, 1.0, 0.0]

        childs = [
            self.spline_controlpoints,
            self.shape,
            self.spline_curve.object,
            self.coords,
            self.grid,
        ]
        self.task_separator += childs
        self.draw_shape()
        self.update_aoa()
        self.update_grid(drag_release=True)
        self.draw_shape()

        self.spline_controlpoints.on_drag.append(self.on_drag)
        self.spline_controlpoints.drag_release.append(self.on_release)

    def setup_widget(self):
        self.layout.setWidget(0, text_field, QtGui.QLabel("num_points"))
        self.layout.setWidget(0, input_field, self.Qnum_aoa)
        self.layout.setWidget(1, text_field, QtGui.QLabel("spline type"))
        self.layout.setWidget(1, input_field, self.spline_select)

        self.Qnum_aoa.setValue(len(self.spline.controlpoints))
        self.Qnum_aoa.setMaximum(9)
        self.Qnum_aoa.setMinimum(2)
        self.Qnum_aoa.valueChanged.connect(self.update_num)

    def on_drag(self):
        self.update_grid(drag_release=False)
        self.update_aoa()
        return

    def on_release(self):
        self.update_grid(drag_release=True)
        return

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape += [Line_old(self.front, color="grey").object]
        self.shape += [Line_old(self.back, color="grey").object]
        for rib in self.ribs:
            self.shape += [Line_old(rib, color="grey").object]

    def update_aoa(self):
        self.spline.controlpoints = (
            np.array([i[:-1] for i in self.spline_controlpoints.control_pos])
            / self.scale
        ).tolist()
        self.spline_curve.update(
            self.spline.get_sequence(num=self.num_on_drag) * self.scale
        )

    def update_spline_type(self):
        self.spline_controlpoints.control_pos = (
            np.array(self.spline.controlpoints) * self.scale
        )
        self.spline_controlpoints.control_points[-1].constrained = [0.0, 1.0, 0.0]
        self.update_aoa()

    def update_grid(self, drag_release=False):
        self.coords.removeAllChildren()
        pts = self.spline.get_sequence(num=self.num_on_drag)
        self.spline_curve.update(pts * self.scale)
        max_x = max([i[0] for i in pts])
        max_y = max([i[1] for i in pts])
        min_y = min([i[1] for i in pts])

        # transform to scale + transform to degree
        # if min_y > 0 miny = 0
        min_y = (min_y < 0) * min_y
        # create range
        min_y = (min_y // self._grid_y_diff) * self._grid_y_diff
        max_y = ((max_y // self._grid_y_diff) + 1.5) * self._grid_y_diff
        self.coords += [
            graphics.Arrow(
                [[0, 0, 0], [0.0, max_y * self.scale[1] + self._grid_y_diff, 0]]
            )
        ]
        self.coords += [graphics.Arrow([[0, 0, 0], [max_x * 1.3, 0.0, 0]])]

        y_grid = np.arange(
            min_y * self.scale[1],
            max_y * self.scale[1],
            self._grid_y_diff * self.scale[1],
        )

        self._update_grid(self.x_grid, y_grid, drag_release)

    def accept(self):
        self.spline_controlpoints.remove_callbacks()
        super(SpanMappingTool, self).accept()
        self.update_view_glider()

    def reject(self):
        self.spline_controlpoints.remove_callbacks()
        super(SpanMappingTool, self).reject()

    def grid_points(self, grid_x, grid_y):
        return [[x, y] for y in grid_y for x in grid_x]

    def _update_grid(self, grid_x, grid_y, drag_release=False):
        self.grid.removeAllChildren()
        x_points_lower = [[x, grid_y[0], -0.001] for x in grid_x]
        x_points_upper = [[x, grid_y[-1], -0.001] for x in grid_x]
        y_points_lower = [[grid_x[0], y, -0.001] for y in grid_y]
        y_points_upper = [[grid_x[-1], y, -0.001] for y in grid_y]
        for l in zip(x_points_lower, x_points_upper):
            self.grid += [Line_old(l, color="grey").object]
        for l in zip(y_points_lower, y_points_upper):
            self.grid += [Line_old(l, color="grey").object]
        for l in y_points_upper:
            color = coin.SoMaterial()
            color.diffuseColor = [0, 0, 0]
            textsep = coin.SoSeparator()
            text = coin.SoText2()
            trans = coin.SoTranslation()
            trans.translation = l
            text.string = self.text_repr(l[1] * self.value_scale)
            textsep += [color, trans, text]
            self.grid += [textsep]
        interpolation = self.spline.interpolation(SpanMappingTool.num_on_drag)
        if drag_release:
            for i in self.back:
                color = coin.SoMaterial()
                color.diffuseColor = [0, 0, 0]
                textsep = coin.SoSeparator()
                scale = coin.SoScale()
                text = coin.SoAsciiText()
                trans = coin.SoTranslation()
                rot = coin.SoRotationXYZ()
                rot.axis = coin.SoRotationXYZ.Z
                rot.angle.setValue(np.pi / 2)
                scale.scaleFactor = (self.text_scale, self.text_scale, self.text_scale)
                trans.translation = (i[0], i[1], 0.001)
                text.string = self.text_repr(
                    interpolation(i[0]) * self.value_scale * self.scale[1]
                )
                textsep += [color, trans, scale, rot, text]
                self.grid += [textsep]

    def text_repr(self, value):
        return str(round(value / self.scale[1], 2))

    def update_num(self):
        self.spline.numpoints = self.Qnum_aoa.value()
        self.spline_controlpoints.control_pos = (
            np.array(self.spline.controlpoints) * self.scale
        )
        self.spline_controlpoints.control_points[-1].constrained = [0.0, 1.0, 0.0]
        self.update_aoa()


class AoaTool(SpanMappingTool):
    value_scale = 180.0 / np.pi
    scale = np.array([1.0, 10.0])
    grid_y_diff = 1
    widget_name = "AoA"

    def __init__(self, obj):
        super(AoaTool, self).__init__(obj)

    @property
    def spline(self):
        return self.parametric_glider.aoa

    def setup_widget(self):
        super(AoaTool, self).setup_widget()
        self.QGlide = QtGui.QDoubleSpinBox(self.base_widget)
        self.QGlide.setValue(self.parametric_glider.glide)
        self.layout.setWidget(3, text_field, QtGui.QLabel("glidenumber"))
        self.layout.setWidget(3, input_field, self.QGlide)

        self.QGlide.valueChanged.connect(self.update_glide)

    def setup_pivy(self):
        super(AoaTool, self).setup_pivy()
        self.aoa_absolute_curve = Line_old([], color="blue", width=2)
        self.task_separator.addChild(self.aoa_absolute_curve.object)
        self.update_glide()

    def update_aoa(self):
        self.spline.controlpoints = (
            np.array([i[:-1] for i in self.spline_controlpoints.control_pos])
            / self.scale
        ).tolist()

        x_values = self.parametric_glider.shape.rib_x_values
        aoa_values = self.parametric_glider.get_aoa(interpolation_num=self.num_on_drag)
        self.spline_curve.update(
            [
                [x * self.scale[0], aoa * self.scale[1]]
                for x, aoa in zip(x_values, aoa_values)
            ]
        )
        if hasattr(self, "aoa_absolute_curve"):
            self.aoa_absolute_curve.update(
                [
                    [x * self.scale[0], (aoa - aoa_diff) * self.scale[1]]
                    for x, aoa, aoa_diff in zip(x_values, aoa_values, self.aoa_diff)
                ]
            )

    def update_glide(self, *args):
        arc_angles = self.parametric_glider.get_arc_angles()
        self.parametric_glider.glide = self.QGlide.value()
        self.aoa_diff = [
            Rib._aoa_diff(arc_angle, self.parametric_glider.glide)
            for arc_angle in arc_angles
        ]
        self.update_aoa()

    # def get_aoa_absolute(self):
    #    arcangles = self.parametric_glider.get_arc_angles()
    #    for arcangle, aoa in zip()

    def accept(self):
        super(AoaTool, self).accept()

    def text_repr(self, value):
        return "{} °".format(str(round(value / self.scale[1], 2)))


class ZrotTool(SpanMappingTool):
    widget_name = "Z rotation"
    scale = np.array([1.0, 1.0])
    grid_y_diff = 0.2
    value_scale = 1.0


class AirfoilMergeTool(SpanMappingTool):
    value_scale = 1
    scale = np.array([1.0, 1.0])
    grid_y_diff = 1.0
    widget_name = "airfoil span mapping"

    @property
    def spline(self):
        return self.parametric_glider.profile_merge_curve


class BallooningMergeTool(SpanMappingTool):
    value_scale = 1
    scale = np.array([1.0, 1.0])
    grid_y_diff = 1.0
    widget_name = "ballooning span mapping"

    @property
    def spline(self):
        return self.parametric_glider.ballooning_merge_curve
