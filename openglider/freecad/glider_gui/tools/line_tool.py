from __future__ import division

from openglider.glider.glider_2d import LowerNode2D, UpperNode2D, BatchNode2D, Line2D
from _tools import base_tool, input_field, text_field, QtGui
from pivy_primitives_new_new import Line, Marker, Container, coin, COLORS
from pivy_primitives import vector3D


class line_tool(base_tool):
    def __init__(self, obj):
        super(line_tool, self).__init__(obj, widget_name="line tool")
        # jetzt des ganze qt zeugs:
        # 1: ein switcher der zwischen aufhaengepunkten und anderen umschaltet
        #2: ein weiteres form widget
        self.tool_widget = QtGui.QStackedWidget()
        self.tool_layout = QtGui.QFormLayout(self.tool_widget)
        self.setup_widget()

        self.shape = Container()
        self.shape.selection_changed = self.selection_changed
        self.setup_pivy()

    def setup_widget(self):
        self.tool_widget.setWindowTitle("object properties")
        self.form.append(self.tool_widget)

        self.add_doc()

        temp_wid = QtGui.QWidget()
        temp_lay = QtGui.QHBoxLayout(temp_wid)
        self.layout.setWidget(1, input_field, temp_wid)

        self.none_widget = QtGui.QWidget()
        self.line_widget = QtGui.QWidget()
        self.lw_att_wid = QtGui.QWidget()
        self.up_att_wid = QtGui.QWidget()

        self.up_att_lay = QtGui.QFormLayout(self.up_att_wid)
        self.lw_att_lay = QtGui.QFormLayout(self.lw_att_wid)
        self.line_layout = QtGui.QFormLayout(self.line_widget)
        self.none_layout = QtGui.QFormLayout(self.none_widget)

        self.target_length = QtGui.QDoubleSpinBox()
        self.line_layout.setWidget(0, text_field, QtGui.QLabel("target length: "))
        self.line_layout.setWidget(0, input_field, self.target_length)
        self.target_length.valueChanged.connect(self.update_target_length)

        self.attach_x_val = QtGui.QDoubleSpinBox()
        self.attach_y_val = QtGui.QDoubleSpinBox()
        self.attach_z_val = QtGui.QDoubleSpinBox()

        for spinbox in [self.attach_x_val, self.attach_y_val, self.attach_z_val]:
            spinbox.setMaximum(10.)
            spinbox.setMinimum(-10.)
            spinbox.valueChanged.connect(self.update_lw_att_pos)

        self.lw_att_lay.addWidget(self.attach_x_val)
        self.lw_att_lay.addWidget(self.attach_y_val)
        self.lw_att_lay.addWidget(self.attach_z_val)

        self.up_att_force = QtGui.QDoubleSpinBox()
        self.up_att_lay.setWidget(0, text_field, QtGui.QLabel("force"))
        self.up_att_lay.setWidget(0, input_field, self.up_att_force)
        self.up_att_force.valueChanged.connect(self.update_up_att_force)
       
        self.tool_widget.addWidget(self.none_widget)
        self.tool_widget.addWidget(self.line_widget)
        self.tool_widget.addWidget(self.lw_att_wid)
        self.tool_widget.addWidget(self.up_att_wid)
        self.tool_widget.setCurrentWidget(self.none_widget)

    def add_doc(self):
        self.layout.addWidget(QtGui.QLabel("g...grap element and move it"))
        self.layout.addWidget(QtGui.QLabel("l...create line from 2 points"))
        self.layout.addWidget(QtGui.QLabel("a...add a new point"))
        self.layout.addWidget(QtGui.QLabel("x...delete a point or a line"))
        self.layout.addWidget(QtGui.QLabel("cltr + a...attachment point"))
        self.layout.addWidget(QtGui.QLabel("cltr...multiselection"))

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
            if (isinstance(obj, ConnectionLine) and not
                (isinstance(obj.marker1, Upper_Att_Marker) or
                 isinstance(obj.marker2, Upper_Att_Marker))):
                self.tool_widget.setCurrentWidget(self.line_widget)
                self.target_length.setValue(obj.target_length)
            elif isinstance(obj, Lower_Att_Marker):
                self.tool_widget.setCurrentWidget(self.lw_att_wid)
                x, y, z = obj.pos3D
                self.attach_x_val.setValue(x)
                self.attach_y_val.setValue(y)
                self.attach_z_val.setValue(z)
            elif isinstance(obj, Upper_Att_Marker):
                self.tool_widget.setCurrentWidget(self.up_att_wid)
                self.up_att_force.setValue(obj.force)

            else:
                self.tool_widget.setCurrentWidget(self.none_widget)
        else:
            self.tool_widget.setCurrentWidget(self.none_widget)

    def update_target_length(self, *args):
        try:
            l = float(self.target_length.value())
            self.shape.select_object[0].target_length = l
        except Exception:
            print(Exception)

    def update_lw_att_pos(self, *args):
        try:
            x = self.attach_x_val.value()
            y = self.attach_y_val.value()
            z = self.attach_z_val.value()
            self.shape.select_object[0].pos3D = [x,y,z]
        except Exception:
            print(Exception)

    def update_up_att_force(self, *args):
        try:
            self.shape.select_object[0].force = self.up_att_force.value()
        except Exception:
            print(Exception)

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
                    line = ConnectionLine(objs[0], objs[1])
                    self.shape.addChild(line)
            elif len(objs) == 1:
                if (isinstance(objs[0], LineMarker)):
                    marker2 = self.point_cb(event_callback, force=True)
                    if marker2:
                        line = ConnectionLine(objs[0], marker2)
                        self.shape.addChild(line)
                        self.shape.Select(marker2)
                        self.shape.selection_changed()

    def point_cb(self, event_callback, force=False):
        event = event_callback.getEvent()
        if ((event.getKey() == ord("a") or force) and
            (event.getState() == 1 or event.wasCtrlDown())):
            pos = event.getPosition()
            pos3D = self.view.getPoint(*pos)
            pos3D[-1] = 0.
            if event.wasCtrlDown():
                point = Lower_Att_Marker(pos3D)
            else:
                point = LineMarker(pos3D)
            self.shape.addChild(point)
            return point

    def draw_shape(self):
        ribs, front, back = map(vector3D, self.glider_2d.shape())
        self.shape.removeAllChildren()
        self.shape.addChild(Line(front))
        self.shape.addChild(Line(back))
        self.shape.addChildren(map(Line, ribs))
        for i in self.glider_2d.lineset.nodes:
            if isinstance(i, UpperNode2D):
                coord = self.glider_2d.shape_point(i.rib_no, i.position/100)
                obj = Upper_Att_Marker(vector3D(coord))
                obj.temp_2d = i
                obj.force = i.force
                self.shape.addChild(obj)
            elif isinstance(i, BatchNode2D):
                obj = LineMarker(vector3D(i.pos_2d))
                obj.temp_2d = i
                self.shape.addChild(obj)
            elif isinstance(i, LowerNode2D):
                obj = Lower_Att_Marker(vector3D(i.pos))
                obj.pos3D = i.pos3D
                obj.temp_2d = i
                self.shape.addChild(obj)
            
        for i in self.glider_2d.lineset.lines:
            m1 = self.get_marker(i.lower_node)
            m2 = self.get_marker(i.upper_node)
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

        for obj in self.shape.objects:
            # add the 2d objects to the graphical objects
            if isinstance(obj, Lower_Att_Marker):
                obj.temp_2d = LowerNode2D(list(obj.pos), obj.pos3D)
                points.append(obj.temp_2d)

            elif isinstance(obj, Upper_Att_Marker):
                # allready stored 2d data
                obj.temp_2d.force = obj.force
                points.append(obj.temp_2d)

            elif isinstance(obj, LineMarker):
                obj.temp_2d = BatchNode2D(list(obj.pos))
                points.append(obj.temp_2d)

        for obj in self.shape.objects:
            if isinstance(obj, ConnectionLine):
                l = Line2D(obj.marker1.temp_2d, obj.marker2.temp_2d)
                if not (isinstance(obj.marker1, Upper_Att_Marker) or
                        isinstance(obj.marker2, Upper_Att_Marker)):
                    l.target_length = obj.target_length
                lines.append(l)


        self.glider_2d.lineset.lines = lines
        self.glider_2d.lineset.nodes = points
        self.glider_2d.get_glider_3d(self.obj.glider_instance)
        self.shape.unregister()
        self.remove_all_callbacks()
        self.obj.glider_2d = self.glider_2d
        super(line_tool, self).accept()

    def reject(self):
        self.shape.unregister()
        self.remove_all_callbacks()
        super(line_tool, self).reject()


# wird die position einer leine veraendert so muessen nur die zwei marker positionen aus denen
# die leine besteht veraendert werden. Diesen Markern wurde eine funktion gegeben, die die position
# der leinen beim verschieben mitveraendert. Der Marker bleibt somit zimlich gleich zur
# usrprungsklasse, die Connection-line muss das drag verhalten neu implementiren.
# des haut gut hin!!!


class LineMarker(Marker):
    def __init__(self, pos, std_col="black", ovr_col="red", sel_col="yellow"):
        super(LineMarker, self).__init__([pos], dynamic=True,  std_col=std_col, ovr_col=ovr_col, sel_col=sel_col)
        self.temp_2d = None

    @property
    def pos(self):
        return self.points[0]

    @pos.setter
    def pos(self, pos):
        self.points = [pos]


class Upper_Att_Marker(LineMarker):
    def __init__(self, pos):
        super(Upper_Att_Marker, self).__init__(pos, std_col="blue")
        self.force = 1.

    def drag(self, *arg):
        pass

    def delete(self):
        pass

class Lower_Att_Marker(LineMarker):
    def __init__(self, pos):
        super(Lower_Att_Marker, self).__init__(pos, std_col="green")
        self.pos3D = [0, 0, 0]

    @property
    def pos(self):
        return self.points[0]

    @pos.setter
    def pos(self, pos):
        self.points = [pos]


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

    def check_dependency(self):
        if self.marker1._delete or self.marker2._delete:
            self.delete()