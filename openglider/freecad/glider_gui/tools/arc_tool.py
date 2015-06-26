from pivy import coin
from PySide import QtGui

from _tools import base_tool, text_field, input_field, spline_select
from pivy_primitives import Line, ControlPointContainer


class arc_tool(base_tool):

    def __init__(self, obj):
        """adds a symmetric spline to the scene"""
        super(arc_tool, self).__init__(obj, widget_name="arc_tool")

        self.arc_cpc = ControlPointContainer(
            self.glider_2d.arc.controlpoints, self.view)
        self.Qnum_arc = QtGui.QSpinBox(self.base_widget)
        self.spline_select = spline_select(
            [self.glider_2d.arc], self.update_spline, self.base_widget)
        self.shape = coin.SoSeparator()
        self.task_separator.addChild(self.shape)

        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):

        self.Qnum_arc.setMaximum(5)
        self.Qnum_arc.setMinimum(2)
        self.Qnum_arc.setValue(len(self.glider_2d.arc.controlpoints))
        self.glider_2d.arc.numpoints = self.Qnum_arc.value()

        self.layout.setWidget(0, text_field, QtGui.QLabel("arc num_points"))
        self.layout.setWidget(0, input_field, self.Qnum_arc)
        self.layout.setWidget(1, text_field, QtGui.QLabel("bspline type"))
        self.layout.setWidget(1, input_field, self.spline_select)

        self.Qnum_arc.valueChanged.connect(self.update_num)

    def setup_pivy(self):
        self.arc_cpc.on_drag.append(self.update_spline)
        self.arc_cpc.drag_release.append(self.update_real_arc)
        self.task_separator.addChild(self.arc_cpc)
        self.shape.addChild(
            Line(self.glider_2d.arc.get_sequence(num=30), 
                 color="grey").object)
        self.shape.addChild(
            Line(self.glider_2d.get_arc_positions(), 
                 color="red", width=2).object)

    # def set_edit(self, *arg):
    #     self.arc_cpc.set_edit_mode(self.view)

    def update_spline(self):
        self.shape.removeAllChildren()
        self.glider_2d.arc.controlpoints = [i[:-1] for i in self.arc_cpc.control_pos]
        self.shape.addChild(Line(self.glider_2d.arc.get_sequence(num=30), color="grey").object)

    def update_real_arc(self):
        self.shape.addChild(Line(self.glider_2d.get_arc_positions(), color="red", width=2).object)

    def update_num(self, *arg):
        self.glider_2d.arc.numpoints = self.Qnum_arc.value()
        self.arc_cpc.control_pos = self.glider_2d.arc.controlpoints
        self.update_spline()

    def accept(self):
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.get_glider_3d(self.obj.glider_instance)
        self.arc_cpc.remove_callbacks()
        self.obj.ViewObject.Proxy.updateData()
        super(arc_tool, self).accept()

    def reject(self):
        self.arc_cpc.remove_callbacks()
        super(arc_tool, self).reject()
