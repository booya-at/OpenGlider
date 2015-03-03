from __future__ import division
import numpy
from pivy import coin
from PySide import QtGui

from _tools import base_tool, text_field, input_field
from pivy_primitives import Line, ControlPointContainer, vector3D


class aoa_tool(base_tool):

    def __init__(self, obj):
        super(aoa_tool, self).__init__(obj)
        self.scale = numpy.array([1., 5.])
        pts = vector3D(numpy.array(self.glider_2d.aoa.controlpoints) * self.scale)
        self.aoa_cpc = ControlPointContainer(pts, self.view)
        self.shape = coin.SoSeparator()
        self.coords = coin.SoSeparator()
        self.grid = coin.SoSeparator()
        self.aoa_spline = Line([])
        self.ribs, self.front, self.back = self.glider_2d.shape()
        self.x_grid = [i[0] for i in self.front]

        self.QGlide = QtGui.QDoubleSpinBox(self.base_widget)
        self.Qnum_aoa = QtGui.QSpinBox(self.base_widget)

        self.setup_widget()
        self.setup_pivy()

    def setup_pivy(self):
        self.aoa_cpc.control_points[-1].constraint = lambda pos: [self.glider_2d.span / 2, pos[1], pos[2]]
        self.task_separator.addChild(self.aoa_cpc)
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.aoa_spline.object)
        self.task_separator.addChild(self.coords)
        self.task_separator.addChild(self.grid)
        self.update_aoa()
        self.draw_shape()

    def setup_widget(self):
        self.QGlide.setValue(self.glider_2d.glide)
        self.layout.setWidget(0, text_field, QtGui.QLabel("glidenumber"))
        self.layout.setWidget(0, input_field, self.QGlide)
        self.layout.setWidget(1, text_field, QtGui.QLabel("num_points"))
        self.layout.setWidget(1, input_field, self.Qnum_aoa)

        self.Qnum_aoa.setValue(len(self.glider_2d.aoa.controlpoints))
        self.Qnum_aoa.setMaximum(5)
        self.Qnum_aoa.setMinimum(2)
        self.Qnum_aoa.valueChanged.connect(self.update_num)
        self.aoa_cpc.on_drag.append(self.update_aoa)

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.front, color="gray").object)
        self.shape.addChild(Line(self.back, color="gray").object)
        for rib in self.ribs:
            self.shape.addChild(Line(rib, color="gray").object)

    def update_aoa(self):
        self.glider_2d.aoa.controlpoints = (numpy.array([i[:-1] for i in self.aoa_cpc.control_pos]) / self.scale).tolist()
        self.aoa_spline.update(self.glider_2d.aoa.get_sequence(num=20) * self.scale)
        self.coords.removeAllChildren()
        max_x = max([i[0] for i in self.aoa_cpc.control_pos])
        max_y = max([i[1] for i in self.aoa_cpc.control_pos])
        min_y = min([i[1] for i in self.aoa_cpc.control_pos])

        self.coords.addChild(Line([[0, 0], [0., max_y * 1.3]]).object)
        self.coords.addChild(Line([[0, 0], [max_x * 1.3, 0.]]).object)
        # transform to scale + transform to degree
        min_y *= 180 / numpy.pi / self.scale[1]
        max_y *= 180 / numpy.pi / self.scale[1]
        # if min_y > 0 miny = 0
        min_y = (min_y < 0) * min_y
        # create range
        _range = range(int(max_y) - int(min_y) + 2)
        # transform back
        y_grid = [(i + int(min_y)) * numpy.pi * self.scale[1] / 180 for i in _range]
        self.update_grid(self.x_grid, y_grid)


    def accept(self):
        self.aoa_cpc.remove_callbacks()
        self.glider_2d.glide = self.QGlide.value()
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.get_glider_3d(self.obj.glider_instance)
        super(aoa_tool, self).accept()

    def reject(self):
        self.aoa_cpc.remove_callbacks()
        super(aoa_tool, self).reject()

    def grid_points(self, grid_x, grid_y):
        return [[x, y] for y in grid_y for x in grid_x]

    def update_grid(self, grid_x, grid_y):
        self.grid.removeAllChildren()
        x_points_lower = [[x, grid_y[0], 0] for x in grid_x]
        x_points_upper = [[x, grid_y[-1], 0] for x in grid_x]
        y_points_lower = [[grid_x[0], y, 0] for y in grid_y]
        y_points_upper = [[grid_x[-1], y, 0] for y in grid_y]
        for l in zip(x_points_lower, x_points_upper):
            self.grid.addChild(Line(l, color="gray").object)
        for l in zip(y_points_lower, y_points_upper):
            self.grid.addChild(Line(l, color="gray").object)

    def update_num(self, *arg):
        self.glider_2d.aoa.numpoints = self.Qnum_aoa.value()
        self.aoa_cpc.control_pos = vector3D(numpy.array(self.glider_2d.aoa.controlpoints) * self.scale)
        self.aoa_cpc.control_points[-1].constraint = lambda pos: [self.glider_2d.span / 2, pos[1], pos[2]]
        self.update_aoa()
