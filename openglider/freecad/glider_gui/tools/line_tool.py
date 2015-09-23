from __future__ import division

import traceback
import numpy as np
import FreeCAD as App

from _tools import base_tool, input_field, text_field
from pivy_primitives_new_new import coin, Line, Marker, Container, vector3D
from PySide import QtGui, QtCore
from openglider.glider.glider_2d import UpperNode2D, LowerNode2D, \
    BatchNode2D, Line2D, LineSet2D
from openglider.lines.line_types import LineType


# all line info goes into the tool.
# the lineset will be totally reloaded after the tool work is ready
# if an error occurs nothing will happen

# 1: create markers from existing lineset
# 2: create lines from existing lineset
# 3: eventhandler for adding and connecting lines

class line_tool(base_tool):
    def __init__(self, obj):
        super(line_tool, self).__init__(obj, widget_name="line_tool")

        # get the glider_2d shape
        self.ribs, self.front, self.back = self.glider_2d.shape().ribs_front_back
        self.xpos = [rib[0][0] for rib in self.glider_2d.ribs()]

        # qt helper line
        self.Qhl_pos = QtGui.QDoubleSpinBox()

        # pivy helper line
        self.helper_line = coin.SoSeparator()
        self.temp_point = coin.SoSeparator()

        # qt element widget
        self.tool_widget = QtGui.QStackedWidget()
        self.tool_layout = QtGui.QFormLayout(self.tool_widget)

        # qt layer widget
        self.layer_widget = QtGui.QWidget()
        self.layer_layout = QtGui.QFormLayout(self.layer_widget)

        # pivy lines, points, shape
        self.shape = Container()
        self.shape.selection_changed = self.selection_changed

        # initialize qt and pivy
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        self.tool_widget.setWindowTitle("object properties")
        self.layer_widget.setWindowTitle("layers")
        self.form.append(self.layer_widget)
        self.form.append(self.tool_widget)

        # temp_wid = QtGui.QWidget()
        # temp_lay = QtGui.QHBoxLayout(temp_wid)
        # self.layout.setWidget(1, input_field, temp_wid)

        self.none_widget = QtGui.QWidget()
        self.line_widget = QtGui.QWidget()
        self.lw_att_wid = QtGui.QWidget()
        self.up_att_wid = QtGui.QWidget()
        self.multi_wid = QtGui.QWidget()
        self.Qline_list = QtGui.QListWidget()
        for _type in LineType.types.values():
            self.Qline_list.addItem(QLineType_item(_type))

        self.up_att_lay = QtGui.QFormLayout(self.up_att_wid)
        self.lw_att_lay = QtGui.QFormLayout(self.lw_att_wid)
        self.line_layout = QtGui.QFormLayout(self.line_widget)
        self.multi_layout = QtGui.QFormLayout(self.multi_wid)
        self.none_layout = QtGui.QFormLayout(self.none_widget)

        self.target_length = QtGui.QDoubleSpinBox()
        self.line_layout.setWidget(
            0, text_field, QtGui.QLabel("target length: "))
        self.line_layout.setWidget(0, input_field, self.target_length)
        self.line_layout.setWidget(1, text_field, QtGui.QLabel("line type: "))
        self.line_layout.setWidget(1, input_field, self.Qline_list)
        self.target_length.valueChanged.connect(self.update_target_length)
        self.Qline_list.currentItemChanged.connect(self.update_line_type)

        self.attach_x_val = QtGui.QDoubleSpinBox()
        self.attach_y_val = QtGui.QDoubleSpinBox()
        self.attach_z_val = QtGui.QDoubleSpinBox()

        for spinbox in [
                self.attach_x_val, self.attach_y_val, self.attach_z_val]:
            spinbox.setMaximum(10.)
            spinbox.setMinimum(-10.)
            spinbox.valueChanged.connect(self.update_lw_att_pos)

        self.lw_att_lay.addWidget(self.attach_x_val)
        self.lw_att_lay.addWidget(self.attach_y_val)
        self.lw_att_lay.addWidget(self.attach_z_val)

        self.up_att_force = QtGui.QDoubleSpinBox()
        self.up_att_force.setSingleStep(0.1)
        self.up_att_lay.setWidget(0, text_field, QtGui.QLabel("force"))
        self.up_att_lay.setWidget(0, input_field, self.up_att_force)
        self.up_att_force.valueChanged.connect(self.update_up_att_force)

        self.tool_widget.addWidget(self.none_widget)
        self.tool_widget.addWidget(self.line_widget)
        self.tool_widget.addWidget(self.lw_att_wid)
        self.tool_widget.addWidget(self.up_att_wid)
        self.tool_widget.setCurrentWidget(self.none_widget)

        button = QtGui.QPushButton("Help")
        self.layout.setWidget(0, input_field, button)
        button.clicked.connect(self.show_help)

        self.Qhl_pos.setValue(50)
        self.Qhl_pos.setRange(0, 100)
        self.Qhl_pos.setSingleStep(1)
        self.Qhl_pos.connect(
            self.Qhl_pos,
            QtCore.SIGNAL('valueChanged(double)'),
            self.update_helper_line)

        self.layout.setWidget(1, text_field, QtGui.QLabel("helper_line_pos"))
        self.layout.setWidget(1, input_field, self.Qhl_pos)

        # layers:

        self.layer_selection = LayerComboBox(self.layer_widget)
        self.layer_combobox = LayerComboBox(self.layer_widget)

        add_button = QtGui.QPushButton("add layer")
        del_button = QtGui.QPushButton("delete layer")
        self.layer_layout.setWidget(
            0, text_field, QtGui.QLabel("work on layer"))
        self.layer_layout.setWidget(0, input_field, self.layer_combobox)
        self.layer_layout.setWidget(1, text_field, add_button)
        self.layer_layout.setWidget(1, input_field, del_button)
        self.layer_layout.setWidget(2, text_field, QtGui.QLabel("setLayer"))
        self.layer_layout.setWidget(2, input_field, self.layer_selection)

        # dialogs
        self.add_layer_dialog = QtGui.QInputDialog()
        add_button.clicked.connect(self.add_new_layer)
        del_button.clicked.connect(self.delete_layer)
        self.layer_combobox.currentIndexChanged.connect(self.show_layer)
        self.layer_selection.activated.connect(self.set_layer_by_current)
        self.layer_selection.setEnabled(False)

    def add_new_layer(self):
        self.add_layer_dialog.exec_()
        text = self.add_layer_dialog.textValue()
        self.layer_combobox.addItem(text)
        index = self.layer_combobox.findText(text)
        self.layer_combobox.setCurrentIndex(index)
        self.set_layer(text=text)
        self.show_layer()
        self.update_layer_selection()

    def delete_layer(self):
        current_layer = self.layer_combobox.currentText()
        self.set_layer(text="", objects=self.shape.objects,
                       from_layer=current_layer)
        self.layer_combobox.removeItem(self.layer_combobox.currentIndex())
        self.update_layer_selection()
        self.show_layer()
        self.update_layer_selection()

    def update_layer_selection(self):
        self.layer_selection.getAllItems(self.layer_combobox)
        self.selection_changed()

    def set_layer_by_current(self):
        self.set_layer()
        self.show_layer()

    def set_layer(self, text=None, objects=None, from_layer=None):
        text = text or self.layer_selection.currentText()
        print("set text to : ", text)
        objects = objects or self.shape.select_object
        for obj in objects:
            if hasattr(obj, "layer"):
                if from_layer is None or from_layer == obj.layer:
                    obj.layer = text

    def show_layer(self):
        for obj in self.shape.objects:
            if hasattr(obj, "layer"):
                if obj.layer != self.layer_combobox.currentText():
                    if obj.enabled:
                        obj.set_disabled()
                else:
                    if not obj.enabled:
                        obj.set_enabled()


    def show_help(self):
        App.Console.PrintMessage("Use this commands to rule the lineinput\n")
        App.Console.PrintMessage("g...grap element and move it\n")
        App.Console.PrintMessage("l...create line from 2 points\n")
        App.Console.PrintMessage("a...add a new point\n")
        App.Console.PrintMessage("x...delete a point or a line\n")
        App.Console.PrintMessage("cltr + a...attachment point\n")
        App.Console.PrintMessage("cltr...multiselection\n")

    def setup_pivy(self):
        self.shape.setName("shape")
        self.shape.register(self.view)
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.helper_line)
        self.task_separator.addChild(self.temp_point)
        self.draw_shape()

        self.update_helper_line()
        self.setup_cb()

    def setup_cb(self):
        self.point_preview_cb = self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.point_preview)
        self.line_cb = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.add_line)
        self.node_cb = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.add_node)

    def remove_all_callbacks(self):
        if self.point_preview_cb:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.point_preview_cb)
        if self.line_cb:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.line_cb)
        if self.node_cb:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.node_cb)

    def update_helper_line(self, pos=50):
        self.helper_line.removeAllChildren()
        l = Line(vector3D(self.help_line(pos / 100)), dynamic=False)
        l.set_color("red")
        self.helper_line.addChild(l)

    def help_line(self, pos=0.5):
        return [fr + pos * (ba - fr) for fr, ba in np.array(self.ribs)]

    def point_preview(self, event_callback, force=False):
        event = event_callback.getEvent()
        self.temp_point.removeAllChildren()
        if type(event) == coin.SoLocation2Event or force:
            self.upper_preview_node = None
            pos = event.getPosition()
            check_points = [i.tolist() for i in self.help_line(self.Qhl_pos.value() / 100)]
            for i, point in enumerate(check_points):
                s = self.view.getPointOnScreen(point[0], point[1], 0.)
                if (abs(s[0] - pos[0]) ** 2 + abs(s[1] - pos[1]) ** 2) < (15 ** 2) and point[0] >= 0:
                    self.upper_preview_node = (point, i)
                    m = Marker(vector3D([point]), dynamic=False)
                    m.set_color("blue")
                    self.temp_point.addChild(m)
                    break

    def add_line(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord("l") and
            event.getState() == 1):
            objs = self.shape.select_object
            if len(objs) == 2:
                if (isinstance(objs[0], NodeMarker) and
                    isinstance(objs[1], NodeMarker)):
                    line = ConnectionLine(objs[0], objs[1])
                    line.layer = self.layer_combobox.currentText()
                    self.shape.addChild(line)
            elif len(objs) == 1:
                if (isinstance(objs[0], NodeMarker)):
                    marker2 = self.node_cb(event_callback, force=True)
                    if marker2:
                        line = ConnectionLine(objs[0], marker2)
                        self.shape.addChild(line)
                        self.shape.Select(marker2)
                        self.shape.selection_changed()
                        line.layer = self.layer_combobox.currentText()

    def add_node(self, event_callback, force=False):
        event = event_callback.getEvent()
        if ((event.getKey() == ord("a") or force) and
            (event.getState() == 1 or event.wasCtrlDown())):
            if self.upper_preview_node:
                self.add_attachment_point(self.upper_preview_node[0])
            else:
                pos = event.getPosition()
                pos_3D = list(self.view.getPoint(*pos))
                pos_3D[-1] = 0.
                if event.wasCtrlDown():
                    node = LowerNode2D(pos_3D[:-1], [0, 0, 0])
                    point = Lower_Att_Marker(node)
                    point.layer = self.layer_combobox.currentText()
                else:
                    node = BatchNode2D(pos_3D[:-1])
                    point = NodeMarker(node)
                    point.layer = self.layer_combobox.currentText()
                self.shape.addChild(point)
                return point

    def add_attachment_point(self, pos):
        x, y = pos
        rib_nr = self.xpos.index(x)
        pos = float(self.Qhl_pos.value())
        node = UpperNode2D(rib_nr, pos / 100)
        node_pos = node.get_2d(self.glider_2d)
        ap = Upper_Att_Marker(node, node_pos)
        ap.layer = self.layer_combobox.currentText()
        self.shape.addChild(ap)

    def selection_changed(self):
        # je nach dem welches widget grad selektiert ist
        # soll er ein widget einblenden.
        # wenn mehrere elemente oder keinen ausgewaehlt ist dann nichts auswaehlen
        def show_line_widget(objs):
            for obj in objs:
                if not (isinstance(obj, ConnectionLine)):
                    return False
            return True

        def has_uppermost_line(objs):
            for obj in objs:
                if obj.is_uppermost_line():
                    return True
            return False

        def show_upper_att_widget(objs):
            for obj in objs:
                if not isinstance(obj, Upper_Att_Marker):
                    return False
            return True

        def show_lower_att_widget(objs):
            for obj in objs:
                if not isinstance(obj, Lower_Att_Marker):
                    return False
            return True

        selected_objs = self.shape.select_object
        if selected_objs:
            self.layer_selection.setEnabled(True)
            self.target_length.setEnabled(True)
            self.layer_selection.setItemByText(selected_objs[0].layer)
            if show_line_widget(selected_objs):
                self.tool_widget.setCurrentWidget(self.line_widget)
                if has_uppermost_line(selected_objs):
                    self.target_length.setEnabled(False)                    
                else:
                    self.target_length.setValue(selected_objs[0].target_length)
                line_type_item = self.Qline_list.findItems(
                        selected_objs[0].line_type, QtCore.Qt.MatchExactly)[0]
                self.Qline_list.setCurrentItem(line_type_item)
            elif show_lower_att_widget(selected_objs):
                self.tool_widget.setCurrentWidget(self.lw_att_wid)
                x, y, z = selected_objs[0].pos_3D
                self.attach_x_val.setValue(x)
                self.attach_y_val.setValue(y)
                self.attach_z_val.setValue(z)
            elif show_upper_att_widget(selected_objs):
                self.tool_widget.setCurrentWidget(self.up_att_wid)
                self.up_att_force.setValue(selected_objs[0].force)
            else:
                self.tool_widget.setCurrentWidget(self.multi_wid)
        else:
            self.tool_widget.setCurrentWidget(self.none_widget)
            self.layer_selection.setEnabled(False)

    def update_target_length(self, *args):
        l = float(self.target_length.value())
        for obj in self.shape.select_object:
            obj.target_length = l

    def update_line_type(self, *args):
        print("update line_type")
        for obj in self.shape.select_object:
            obj.line_type = self.Qline_list.currentItem().line_type.name

    def update_lw_att_pos(self, *args):
        x = self.attach_x_val.value()
        y = self.attach_y_val.value()
        z = self.attach_z_val.value()
        for obj in self.shape.select_object:
            obj.pos_3D = [x,y,z]

    def update_up_att_force(self, *args):
        for obj in self.shape.select_object:
            obj.force = self.up_att_force.value()

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(vector3D(self.front)))
        self.shape.addChild(Line(vector3D(self.back)))
        self.shape.addChildren(map(Line, vector3D(self.ribs)))
        # make own seperator for shape
        nodes = {}
        for node in self.glider_2d.lineset.nodes:
            if isinstance(node, UpperNode2D):
                # coord = self.glider_2d.shape_point(node.rib_no, node.position/100)
                pos = node.get_2d(self.glider_2d)
                obj = Upper_Att_Marker(node, pos)
                obj.force = node.force
                self.shape.addChild(obj)
            elif isinstance(node, BatchNode2D):
                obj = NodeMarker(node)
                self.shape.addChild(obj)
            elif isinstance(node, LowerNode2D):
                obj = Lower_Att_Marker(node)
                obj.pos_3D = node.pos_3D
                obj._node = node
                self.shape.addChild(obj)
            nodes[node] = obj
            self.layer_combobox.addItem(node.layer)

        for line in self.glider_2d.lineset.lines:
            m1 = nodes[line.lower_node]
            m2 = nodes[line.upper_node]
            target_length = line.target_length
            obj = ConnectionLine(m1, m2)
            obj.line_type = line.line_type.name
            obj.target_length = target_length
            obj.layer = line.layer
            self.shape.addChild(obj)
            self.layer_combobox.addItem(line.layer)
        self.show_layer()

    def accept(self):
        """glider 2d will recive the 2d information
            the attachmentpoints are already stored.
            the other points are stored into the batch_points list
        """
        lines = []

        for obj in self.shape.objects:
            if isinstance(obj, ConnectionLine):
                l = Line2D(obj.marker1.node, obj.marker2.node)
                if not obj.is_uppermost_line():
                    l.target_length = obj.target_length
                l.line_type = LineType.types[obj.line_type]
                l.layer = obj.layer
                lines.append(l)

        lineset = self.glider_2d.lineset
        try:
            new_lines = LineSet2D(lines)
            self.glider_2d.lineset = new_lines
            self.glider_2d.get_glider_3d(self.obj.glider_instance)
        except Exception as e:
            App.Console.PrintError(traceback.format_exc())
            self.glider_2d.lineset = lineset
            self.glider_2d.get_glider_3d(self.obj.glider_instance)
            return

        for node in self.glider_2d.lineset.nodes:
            if isinstance(node, UpperNode2D):
                node.name = node.layer + str(node.rib_no)

        self.shape.unregister()
        self.remove_all_callbacks()
        self.obj.glider_2d = self.glider_2d
        super(line_tool, self).accept()
        
    def reject(self):
        self.shape.unregister()
        self.remove_all_callbacks()
        super(line_tool, self).reject()


class NodeMarker(Marker):
    std_col = "black"
    ovr_col = "red"
    sel_col = "yellow"

    def __init__(self, node, pos=None):
        pos = pos or node.pos_2D
        pos = vector3D(pos)
        super(NodeMarker, self).__init__([pos], dynamic=True)
        self._node = node

    @property
    def node(self):
        self._node.pos_2D = list(self.pos)[:-1]
        return self._node

    @property
    def pos(self):
        return self.points[0]

    @pos.setter
    def pos(self, pos):
        self.points = [pos]

    @property
    def layer(self):
        return self._node.layer

    @layer.setter
    def layer(self, layer):
        self._node.layer = layer


class Upper_Att_Marker(NodeMarker):
    std_col = "blue"

    def __init__(self, node, pos):
        super(Upper_Att_Marker, self).__init__(node, pos)

    @property
    def force(self):
        return self._node.force

    @force.setter
    def force(self, value):
        self._node.force = value

    def drag(self, *arg):
        pass


class Lower_Att_Marker(NodeMarker):
    std_col = "green"

    def __init__(self, node):
        pos = node.pos_2D
        super(Lower_Att_Marker, self).__init__(node, pos)

    @property
    def pos_3D(self):
        return self._node.pos_3D

    @pos_3D.setter
    def pos_3D(self, value):
        self._node.pos_3D = value

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
        self.drawstyle.lineWidth = 1.
        self.target_length = 1.
        self.line_type = "default"
        self.layer = ""

    def is_uppermost_line(self):
        return (isinstance(self.marker1, Upper_Att_Marker) or 
                isinstance(self.marker2, Upper_Att_Marker))

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

class QLineType_item(QtGui.QListWidgetItem):
    def __init__(self, line_type):
        self.line_type = line_type
        super(QLineType_item, self).__init__()
        self.setText(self.line_type.name)

class LayerComboBox(QtGui.QComboBox):
    def __init__(self, parent=None):
        super(LayerComboBox, self).__init__(parent)
        self.setInsertPolicy(QtGui.QComboBox.InsertAlphabetically)
        self.addItem("")

    def addItem(self, text):
        if self.findText(text) == -1:
            super(LayerComboBox, self).addItem(text)

    def removeItem(self, index):
        super(LayerComboBox, self).removeItem(index)
        if self.count() == 0:
            self.addItem("")

    def removeAll(self):
        while self.currentIndex() != -1:
            super(LayerComboBox, self).removeItem(self.currentIndex())

    def getAllItems(self, other):
        self.removeAll()
        for i in range(other.count()):
            self.addItem(other.itemText(i))

    def currentText(self):
        print("current Item", self.currentIndex())
        print("current Text", self.itemText(self.currentIndex()))

        return self.itemText(self.currentIndex())

    def setItemByText(self, text):
        item = self.findText(text)
        if item != -1:
            self.setCurrentIndex(item)
