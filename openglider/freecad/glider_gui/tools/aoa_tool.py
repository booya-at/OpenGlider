import numpy
from pivy import coin
from PySide import QtGui

from _tools import base_tool, text_field, input_field
from pivy_primitives import Line, ControlPointContainer, vector3D


class aoa_tool(base_tool):

    def __init__(self, obj):
        super(aoa_tool, self).__init__(obj)
        self.scale = numpy.array([1., 5.])
        self.aoa_cpc = ControlPointContainer(vector3D(numpy.array(self.glider_2d.aoa.controlpoints) * self.scale), self.view)
        self.shape = coin.SoSeparator()
        self.coords = coin.SoSeparator()
        self.aoa_spline = Line([])
        self.ribs, self.front, self.back = self.glider_2d.shape()

        self.QGlide = QtGui.QDoubleSpinBox(self.base_widget)

        self.aoa_cpc.on_drag.append(self.update_aoa)
        self.setup_widget()
        self.setup_pivy()

    def setup_pivy(self):
        self.aoa_cpc.control_points[-1].constraint = lambda pos: [self.glider_2d.span / 2, pos[1], pos[2]]
        self.task_separator.addChild(self.aoa_cpc)
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.aoa_spline.object)
        self.task_separator.addChild(self.coords)
        self.update_aoa()
        self.draw_shape()

    def setup_widget(self):
        self.QGlide.setValue(self.glider_2d.glide)
        self.layout.setWidget(0, text_field, QtGui.QLabel("glidenumber"))
        self.layout.setWidget(0, input_field, self.QGlide)

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
        self.coords.addChild(Line([[0, 0], [0., max_y]]).object)
        self.coords.addChild(Line([[0, 0], [max_x, 0.]]).object)

    def accept(self):
        self.aoa_cpc.remove_callbacks()
        self.glider_2d.glide = self.QGlide.value()
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.get_glider_3d(self.obj.glider_instance)
        super(aoa_tool, self).accept()

    def reject(self):
        self.aoa_cpc.remove_callbacks()
        super(aoa_tool, self).reject()
