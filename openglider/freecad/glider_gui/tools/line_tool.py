from __future__ import division

from _tools import base_tool, input_field, text_field, QtGui
from pivy_primitives_new_new import Line, Marker, Container, coin
from pivy_primitives import vector3D

class line_tool(base_tool):
    def __init__(self, obj):
        super(line_tool, self).__init__(obj, widget_name="line tool")

        # als erstes die listen wo des zeug gespeichert wird
        self.point_list = []  #da kommen alle punkte rein
        self.line_list = []  #da kommen alle leinen eini

        # jetzt des ganze qt zeugs:
        # 1: ein switcher der zwischen aufhaengepunkten und anderen umschaltet
        self.toggle_tool = QtGui.QPushButton(self.base_widget)
        #2: ein weiteres form widget
        self.tool_widget = QtGui.QWidget()
        self.tool_layout = QtGui.QFormLayout(self.tool_widget)
        self.setup_widget()

        self.shape = Container()
        self.setup_pivy()


    def setup_widget(self):
        self.tool_widget.setWindowTitle("toolz")
        self.form.append(self.tool_widget)

        self.toggle_tool.clicked.connect(self.change_tool)
        self.layout.setWidget(1, text_field, QtGui.QLabel("switch tha tool"))
        self.layout.setWidget(1, input_field, self.toggle_tool)

        self.tool_layout.setWidget(1, text_field, QtGui.QLabel("check out"))

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
        att_pos = map(vector3D, self.glider_2d.attachment_points)
        self.shape.addChildren(map(Attachment_Marker, att_pos))


    def change_tool(self, *arg):
        # switching between attachmentpoints and buendlepunkte
        pass

    def remove_all_callbacks(self):
        if self.add_line:
            self.view.removeEventCallbackPivy(
                coin.SoKeyboardEvent.getClassTypeId(), self.add_line)
        if self.add_point:
            self.view.removeEventCallbackPivy(
                coin.SoKeyboardEvent.getClassTypeId(), self.add_point)


    def accept(self):
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

    @property
    def pos(self):
        return(self.points[0])

    @pos.setter
    def pos(self, pos):
        self.points = [pos]


class Attachment_Marker(LineMarker):
    def drag(self, *arg):
        pass


class ConnectionLine(Line):
    def __init__(self, marker1, marker2):
        super(ConnectionLine, self).__init__([marker1.pos, marker2.pos], dynamic=True)
        self.marker1 = marker1
        self.marker2 = marker2
        self.marker1.on_drag.append(self.update_Line)
        self.marker2.on_drag.append(self.update_Line)

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
