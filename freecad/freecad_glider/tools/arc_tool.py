import FreeCADGui as Gui
from pivy import coin
import numpy

from openglider.vector.polygon import CirclePart
from PySide import QtGui

from pivy.graphics import InteractionSeparator, Line, Point, Marker

from .tools import (BaseTool, input_field, spline_select, text_field, 
                    vector3D, vector2D, ControlPointContainer)



class ArcTool(BaseTool):
    hide = False
    widget_name = 'ArcTool'

    def __init__(self, obj):
        '''adds a symmetric spline to the scene'''
        super(ArcTool, self).__init__(obj)
        sbrot1 = coin.SbRotation()
        sbrot1.setValue(coin.SbVec3f(1, 0, 0), coin.SbVec3f(0, 1, 0))
        sbrot2 = coin.SbRotation()
        sbrot2.setValue(coin.SbVec3f(0, 0, 1), coin.SbVec3f(0, 1, 0))
        self.obj.ViewObject.Proxy.rotate(sbrot1 * sbrot2)

        controlpoints = list(map(vector3D, self.parametric_glider.arc.curve.controlpoints))
        self.arc_cpc = ControlPointContainer(self.rm, controlpoints)
        self.Qnum_arc = QtGui.QSpinBox(self.base_widget)
        self.spline_select = spline_select(
            [self.parametric_glider.arc.curve], self.update_spline_type, self.base_widget)
        self.shape = coin.SoSeparator()
        self.circle = coin.SoSeparator()
        self.task_separator +=  self.arc_cpc, self.shape, self.circle

        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):

        self.Qnum_arc.setMaximum(9)
        self.Qnum_arc.setMinimum(2)
        self.Qnum_arc.setValue(len(self.parametric_glider.arc.curve.controlpoints))
        self.parametric_glider.arc.curve.numpoints = self.Qnum_arc.value()

        self.layout.setWidget(0, text_field, QtGui.QLabel('arc num_points'))
        self.layout.setWidget(0, input_field, self.Qnum_arc)
        self.layout.setWidget(1, text_field, QtGui.QLabel('bspline type'))
        self.layout.setWidget(1, input_field, self.spline_select)

        self.Qnum_arc.valueChanged.connect(self.update_num)

    def setup_pivy(self):
        self.arc_cpc.on_drag.append(self.update_spline)
        self.arc_cpc.on_drag_release.append(self.update_real_arc)

        self.update_spline()
        self.update_real_arc()
        self.update_num()

    def update_spline(self):
        self.shape.removeAllChildren()
        self.parametric_glider.arc.curve.controlpoints = [vector2D(i) for i in self.arc_cpc.control_pos]
        l = Line(vector3D(self.parametric_glider.arc.curve.get_sequence(num=30)))
        l.drawstyle.lineWidth = 2
        self.shape += l
        self.draw_circle()

    def draw_circle(self):
        self.circle.removeAllChildren()
        sequence = numpy.array(self.parametric_glider.arc.curve.get_sequence(num=30).nodes)
        p1, p2, p3 = sequence[[0, 15, -1]]
        circle = CirclePart(p1, p2, p3)
        self.circle += Line(vector3D(circle.get_sequence()))
        self.circle += Point(vector3D([circle.center]))
        self.circle += Line(vector3D([p2, circle.center, p3]))


    def update_spline_type(self):
        self.arc_cpc.control_pos = self.parametric_glider.arc.curve.controlpoints
        self.update_spline()

    def get_arc_positions(self):
        return self.parametric_glider.arc.get_arc_positions(self.parametric_glider.shape.rib_x_values)

    def update_real_arc(self):
        l = Line(vector3D(self.get_arc_positions()))
        l.drawstyle.lineWidth = 2
        l.set_color("red")
        self.shape += l

    def update_num(self, *arg):
        self.parametric_glider.arc.curve.numpoints = self.Qnum_arc.value()
        self.arc_cpc.control_pos = self.parametric_glider.arc.curve.controlpoints
        self.update_spline()

    def accept(self):
        self.arc_cpc.remove_callbacks()
        super(ArcTool, self).accept()
        self.obj.ViewObject.Proxy.rotate()
        self.update_view_glider()
        Gui.activeDocument().activeView().viewFront()

    def reject(self):
        self.arc_cpc.remove_callbacks()
        self.obj.ViewObject.Proxy.rotate()
        Gui.activeDocument().activeView().viewFront()
        super(ArcTool, self).reject()
