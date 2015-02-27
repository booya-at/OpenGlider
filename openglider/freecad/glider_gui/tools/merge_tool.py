import numpy
from pivy import coin
from PySide import QtGui

from _tools import base_tool, text_field, input_field
from pivy_primitives import Line, ControlPointContainer, vector3D

from openglider.vector.spline import BezierCurve, SymmetricBezier


class base_merge_tool(base_tool):
    def __init__(self, obj):
        super(base_merge_tool, self).__init__(obj)
        self.scale = numpy.array([1., 5.])
        self.bezier_curve = BezierCurve([[0, 0], [1, 1]])
        self.bezier_cpc = ControlPointContainer([], self.view)
        self.shape = coin.SoSeparator()
        self.coords = coin.SoSeparator()
        self.expl_curve = Line([])
        self.ribs, self.front, self.back = self.glider_2d.shape()

        self.bezier_cpc.on_drag.append(self.update_spline)
        self.setup_widget()
        self.setup_pivy()

    def setup_pivy(self):
        self.task_separator.addChild(self.bezier_cpc)
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.expl_curve.object)
        self.task_separator.addChild(self.coords)
        self.update_spline()
        self.draw_shape()

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.front, color="gray").object)
        self.shape.addChild(Line(self.back, color="gray").object)
        for rib in self.ribs:
            self.shape.addChild(Line(rib, color="gray").object)

    def update_num_control_points(self, numpoints):
        self.bezier_curve.numpoints = numpoints
        self.bezier_cpc.control_points[-1].constraint = lambda pos: [self.glider_2d.span / 2, pos[1], pos[2]]

    def update_spline(self):
        pass

    def accept(self):
        self.bezier_cpc.remove_callbacks()
        self.glider_2d.glide = self.QGlide.value()
        self.update_view_glider()
        super(base_merge_tool, self).accept()

    def reject(self):
        self.bezier_curve.remove_callbacks()
        super(base_merge_tool, self).reject()


class airfoil_merge_tool(base_merge_tool):
    pass