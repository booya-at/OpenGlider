from __future__ import division

from openglider.glider.glider_2d import lw_att_point, up_att_point, batch_point, _line
from _tools import base_tool, input_field, text_field, QtGui
from pivy_primitives_new_new import Line, Marker, Container, coin
from pivy_primitives import vector3D

class line_tool(base_tool):
    def __init__(self, obj):
        super(line_tool, self).__init__(obj, widget_name="line tool")
        # jetzt des ganze qt zeugs:
        # 1: ein switcher der zwischen aufhaengepunkten und anderen umschaltet
        #2: ein weiteres form widget
        self.tool_widget = QtGui.QStackedWidget()
        self.attach_x_val = QtGui.QDoubleSpinBox()
        self.attach_y_val = QtGui.QDoubleSpinBox()
        self.attach_z_val = QtGui.QDoubleSpinBox()
        self.tool_layout = QtGui.QFormLayout(self.tool_widget)
        self.setup_widget()

        self.shape = Container()
        self.shape.selection_changed = self.selection_changed
        self.setup_pivy()

    def setup_widget(self):
        self.tool_widget.setWindowTitle("object properties")
        self.form.append(self.tool_widget)

        for spinbox in [self.attach_x_val, self.attach_y_val, self.attach_z_val]:
            spinbox.setMaximum(10.)
            spinbox.setMinimum(-10.)

        temp_wid = QtGui.QWidget()
        temp_lay = QtGui.QHBoxLayout(temp_wid)
        temp_lay.addWidget(self.attach_x_val)
        temp_lay.addWidget(self.attach_y_val)
        temp_lay.addWidget(self.attach_z_val)
        self.layout.setWidget(1, input_field, temp_wid)

        self.none_widget = QtGui.QWidget()
        self.line_widget = QtGui.QWidget()
        self.attachment_widget = QtGui.QWidget()

        self.line_layout = QtGui.QFormLayout(self.line_widget)
        self.none_layout = QtGui.QFormLayout(self.none_widget)

        self.target_length = QtGui.QDoubleSpinBox()
        self.line_layout.setWidget(0, text_field, QtGui.QLabel("target length: "))
        self.line_layout.setWidget(0, input_field, self.target_length)

        self.target_length.valueChanged.connect(self.update_target_length)

        self.tool_widget.addWidget(self.none_widget)
        self.tool_widget.addWidget(self.line_widget)
        self.tool_widget.setCurrentWidget(self.none_widget)

    def setup_pivy(self):
        self.shape.setName("shape")
        # als erstes soll er den shape hinmalen (kommt alles in einen shape seperator)
        self.shape.register(self.view)
        self.task_separator.addChild(self.shape)
        self.draw_shape()
        # jetzt noch die aufhaengepunkte, die aber nicht bewegt werden duerfen
        self.add_line = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.line_cb)
        self.add_point = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.point_cb)



    def selection_changed(self):
        # je nach dem welches widget grad selektiert ist
        # soll er ein widget einblenden.
        # wenn mehrere elemente oder keinen ausgewaehlt ist dann nichts auswaehlen
        if len(self.shape.select_object) == 1:
            obj = self.shape.select_object[0]
            if isinstance(obj, ConnectionLine):
                self.tool_widget.setCurrentWidget(self.line_widget)
                self.target_length.setValue(obj.target_length)
            else:
                self.tool_widget.setCurrentWidget(self.none_widget)
        else:
            self.tool_widget.setCurrentWidget(self.none_widget)

    def update_target_length(self, *args):
        try:
            l = float(self.target_length.value())
            self.shape.select_object[0].target_length = l
        except Exception:
            pass


    def line_cb(self, event_callback):
        # press g to move an entity
        # later let the user select more entities...
        event = event_callback.getEvent()
        if (event.getKey() == ord("l") and
            event.getState() == 1):
            objs = self.shape.select_object
            if len(objs) == 2:
                if (isinstance(objs[0], LineMarker) and
                    isinstance(objs[1], LineMarker)):
                    line =ConnectionLine(objs[0], objs[1])
                    self.shape.addChild(line)

    def point_cb(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord("a") and
            event.getState() == 1):
            pos = event.getPosition()
            pos3D = self.view.getPoint(*pos)
            pos3D[-1] = 0.
            point = LineMarker(pos3D)
            self.shape.addChild(point)

    def draw_shape(self):
        ribs, front, back = map(vector3D, self.glider_2d.shape())
        self.shape.removeAllChildren()
        self.shape.addChild(Line(front))
        self.shape.addChild(Line(back))
        self.shape.addChildren(map(Line, ribs))
        for i in self.glider_2d.lineset.points:
            if isinstance(i, up_att_point):
                coord = i.get_2d(self.glider_2d)
                obj = Attachment_Marker(vector3D(coord))
                obj.temp_2d = i
                self.shape.addChild(obj)
            elif isinstance(i, (batch_point, lw_att_point)):
                obj = LineMarker(vector3D(i.pos))
                obj.temp_2d = i
                self.shape.addChild(obj)
        for i in self.glider_2d.lineset.lines:
            m1 = self.get_marker(i.point1)
            m2 = self.get_marker(i.point2)
            target_length = i.target_length
            obj = ConnectionLine(m1, m2)
            obj.target_length = target_length
            self.shape.addChild(obj)

    def get_marker(self, obj_2d):
        for i in self.shape.objects:
            if isinstance(i, LineMarker):
                if i.temp_2d == obj_2d:
                    return i
        return False

    def remove_all_callbacks(self):
        if self.add_line:
            self.view.removeEventCallbackPivy(
                coin.SoKeyboardEvent.getClassTypeId(), self.add_line)
        if self.add_point:
            self.view.removeEventCallbackPivy(
                coin.SoKeyboardEvent.getClassTypeId(), self.add_point)

    @property
    def lower_attachment_points(self):
        """find all the points that are once attached"""
        once = []
        twice = []
        for obj in self.shape.objects:
            if isinstance(obj, ConnectionLine):
                for i in [obj.marker1, obj.marker2]:
                    if not isinstance(i, Attachment_Marker):
                        if i not in twice:
                            if i not in once:
                                once.append(i)
                            else:
                                once.remove(i)
                                twice.append(i)
        return once

    @property
    def line_is_selected(self):
        #at the moment multiselection isn't supported
        return (len(self.shape.objects) == 1 and
            isinstance(self.shape.objects[0], ConnectionLine))


    def accept(self):
        """glider 2d will recive the 2d information
            the attachmentpoints are already stored.
            the other points are stored into the batch_points list
        """
        lines = []
        points = []

        la = self.lower_attachment_points
        la_pos = [self.attach_x_val.value(),
                  self.attach_y_val.value(),
                  self.attach_z_val.value()]
        for obj in self.shape.objects:
            # add the 2d objects to the graphical objects
            if obj in la:
                obj.temp_2d = lw_att_point(obj.pos, la_pos)
                points.append(obj.temp_2d)

            elif isinstance(obj, Attachment_Marker):
                # allready stored 2d data
                points.append(obj.temp_2d)

            elif isinstance(obj, LineMarker):
                obj.temp_2d = batch_point(obj.pos)
                points.append(obj.temp_2d)

        for obj in self.shape.objects:
            if isinstance(obj, ConnectionLine):
                l = _line(obj.marker1.temp_2d, obj.marker2.temp_2d)
                l.target_length = obj.target_length
                lines.append(l)


        self.glider_2d.lineset.lines = lines
        self.glider_2d.lineset.points = points

        self.shape.unregister()
        self.remove_all_callbacks()
        self.obj.glider_2d = self.glider_2d
        super(line_tool, self).accept()

    def reject(self):
        self.shape.unregister()
        self.remove_cb()
        self.remove_all_callbacks()
        super(line_tool, self).reject()


# wird die position einer leine veraendert so muessen nur die zwei marker positionen aus denen
# die leine besteht veraendert werden. Diesen Markern wurde eine funktion gegeben, die die position
# der leinen beim verschieben mitveraendert. Der Marker bleibt somit zimlich gleich zur
# usrprungsklasse, die Connection-line muss das drag verhalten neu implementiren.
# des haut gut hin!!!


class LineMarker(Marker):
    def __init__(self, pos):
        super(LineMarker, self).__init__([pos], dynamic=True)
        self.temp_2d = None
        self.force = 1.

    @property
    def pos(self):
        return(self.points[0])

    @pos.setter
    def pos(self, pos):
        self.points = [pos]

class Attachment_Marker(LineMarker):
    def __init__(self, pos):
        super(Attachment_Marker, self).__init__(pos)
        self.force = 1.

    def drag(self, *arg):
        pass


class ConnectionLine(Line):
    def __init__(self, marker1, marker2):
        super(ConnectionLine, self).__init__([marker1.pos, marker2.pos], dynamic=True)
        self.marker1 = marker1
        self.marker2 = marker2
        self.marker1.on_drag.append(self.update_Line)
        self.marker2.on_drag.append(self.update_Line)
        self.drawstyle.lineWidth = 2.
        self.target_length = 1.

    def update_Line(self):
        self.points = [self.marker1.pos, self.marker2.pos]

    def drag(self, mouse_coords, fact=1.):
        self.marker1.drag(mouse_coords, fact)
        self.marker2.drag(mouse_coords, fact)

    @property
    def drag_objects(self):
        return [self.marker1, self.marker2]

    @property
    def points(self):
        return self.data.point.getValues()

    @points.setter
    def points(self, points):
        p = [[pi[0], pi[1], pi[2] -0.001] for pi in points]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)
