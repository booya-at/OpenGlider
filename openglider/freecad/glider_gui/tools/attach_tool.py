from __future__ import division

import numpy

from _tools import base_tool, input_field, text_field
from pivy_primitives import Line, Marker, coin
from PySide import QtGui, QtCore
from openglider.glider.glider_2d import UpperNode2D



class attach_tool(base_tool):
    def __init__(self, obj):
        # allow helper curves
        # callback for point visualization (only when mouse near a cutting point)
        super(attach_tool, self).__init__(obj, widget_name="airfoil tool")

        # save the shape as it will not be changed in this task
        self.ribs, self.front, self.back = self.glider_2d.shape()
        self.xpos = numpy.unique([i[0] for i in self.front if i[0]>=0.]).tolist()
        self.current_point = None

        # adding some pivy containers
        self.shape = coin.SoSeparator()
        self.helper_line = coin.SoSeparator()
        self.temp_point = coin.SoSeparator()
        self.vis_point_list = coin.SoSeparator()
        self.setup_pivy()

        # qt gui stuff
        self.Qhelper_lines = QtGui.QWidget()
        self.Qhl_layout = QtGui.QFormLayout(self.Qhelper_lines)
        self.Qhl_pos = QtGui.QDoubleSpinBox(self.Qhelper_lines)
        self.setup_widget()

    def setup_pivy(self):
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.helper_line)
        self.task_separator.addChild(self.temp_point)
        self.task_separator.addChild(self.vis_point_list)
        self.draw_shape()
        self.update_point_list()
        self.update_helper_line()
        self.setup_cb()

    def setup_widget(self):
        self.form.append(self.Qhelper_lines)
        self.Qhl_pos.setValue(50)
        self.Qhl_pos.setRange(0, 100)
        self.Qhl_pos.setSingleStep(1)

        self.Qhelper_lines.connect(self.Qhl_pos, QtCore.SIGNAL('valueChanged(double)'), self.update_helper_line)

        self.Qhl_layout.setWidget(1, text_field, QtGui.QLabel("helper_line_pos"))
        self.Qhl_layout.setWidget(1, input_field, self.Qhl_pos)

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.front).object)
        self.shape.addChild(Line(self.back).object)
        for rib in self.ribs:
            self.shape.addChild(Line(rib).object)

    def update_helper_line(self, pos=50):
        self.helper_line.removeAllChildren()
        self.helper_line.addChild(Line(self.help_line(pos / 100), color="red").object)

    # chached
    def help_line(self, pos=0.5):
        return [fr + pos * (ba - fr) for fr, ba in numpy.array(self.ribs)]

    def setup_cb(self):
        self.point_preview_cb = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.point_preview)
        self.add_point_cb = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.add_point)

    def remove_cb(self):
        if self.point_preview_cb:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.point_preview_cb)
        if self.add_point_cb:
            self.view.removeEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.add_point_cb)

    def point_preview(self, event_callback, force=False):
        event = event_callback.getEvent()
        self.temp_point.removeAllChildren()
        if type(event) == coin.SoLocation2Event or force:
            self.current_point = None
            pos = event.getPosition()
            if event.wasCtrlDown():
                check_points = self.glider_2d.attachment_points
                color = "green"
            else:
                check_points = [i.tolist() for i in self.help_line(self.Qhl_pos.value() / 100)]
                color = "red"
            for i, point in enumerate(check_points):
                s = self.view.getPointOnScreen(point[0], point[1], 0.)
                if (abs(s[0] - pos[0]) ** 2 + abs(s[1] - pos[1]) ** 2) < (15 ** 2) and point[0] >= 0:
                    self.current_point = (point, i)
                    self.temp_point.addChild(Marker([point], color=color))
                    break

    def update_point_list(self):
        self.vis_point_list.removeAllChildren()
        if len(self.glider_2d.attachment_points) > 0:
            self.vis_point_list.addChild(Marker(self.glider_2d.attachment_points))

    def add_point(self, event_callback):
        event = event_callback.getEvent()
        if self.current_point is not None and event.getState():
            if event.wasCtrlDown():  # deleting current point TODO: not working yet
                try:
                    self.glider_2d.lineset.nodes.pop(self.current_point[1])
                    self.current_point = None
                    self.temp_point.removeAllChildren()
                    self.update_point_list()
                    self.point_preview(event_callback, force=True)
                except ValueError:
                    print("whats wrong here???")
            else:  # adding a point
                print("add point")
                self.add_attachment_point(self.current_point[0])
                self.update_point_list()

    def add_attachment_point(self, pos):
        x, y = pos
        rib_nr = self.xpos.index(x)
        pos = float(self.Qhl_pos.value())
        ap = UpperNode2D(rib_nr, pos)
        self.glider_2d.lineset.nodes.append(ap)

    def accept(self):
        self.remove_cb()
        self.obj.glider_2d = self.glider_2d
        super(attach_tool, self).accept()

    def reject(self):
        self.remove_cb()
        super(attach_tool, self).reject()
