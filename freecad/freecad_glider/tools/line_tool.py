from __future__ import division

import sys
if sys.version_info.major > 2:
    from importlib import reload

from PySide import QtGui, QtCore
import traceback
import numpy as np
import FreeCAD as App
import FreeCADGui as Gui

from ._tools import BaseTool, input_field, text_field
from ._glider import draw_glider, draw_lines
from .pivy_primitives_new import vector3D
from .pivy_primitives_new import InteractionSeparator, Object3D, Arrow
from .pivy_primitives_new import Line as _Line
from .pivy_primitives_new import Marker as _Marker
from .pivy_primitives_new import coin

from openglider.glider.parametric.lines import UpperNode2D, LowerNode2D, \
    BatchNode2D, Line2D, LineSet2D
from openglider.lines.line_types import LineType
import numpy as np


def refresh():
    pass

class Line(_Line):
    def set_disabled(self):
        super(Line, self).set_disabled()
        points = np.array(self.points)
        points.T[2] = -1
        self.points = points

    def set_enabled(self):
        super(Line, self).set_enabled()
        points = np.array(self.points)
        points.T[2] = 0
        self.points = points


class Marker(_Marker):
    def set_disabled(self):
        super(Marker, self).set_disabled()
        points = np.array(self.points)
        points.T[2] = -1
        self.points = points

    def set_enabled(self):
        super(Marker, self).set_enabled()
        points = np.array(self.points)
        points.T[2] = 0
        self.points = points


class LineContainer(InteractionSeparator):
    def Select(self, obj, multi=False):
        if not multi:
            for o in self.selected_objects:
                o.unselect()
            self.selected_objects = []
        if obj:
            if obj in self.selected_objects:
                self.selected_objects.remove(obj)
            elif obj.enabled:
                self.selected_objects.append(obj)
        self.ColorSelected()
        self.selection_changed()

    def select_all_cb(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord('a')):
            if event.getState() == event.DOWN:
                if self.selected_objects:
                    for o in self.selected_objects:
                        o.unselect()
                    self.selected_objects = []
                else:
                    for obj in self.objects:
                        if obj.dynamic and obj.enabled:
                            self.selected_objects.append(obj)
                self.ColorSelected()
                self.selection_changed()

# all line info goes into the tool.
# the lineset will be totally reloaded after the tool work is ready
# if an error occurs nothing will happen

# 1: create markers from existing lineset
# 2: create lines from existing lineset
# 3: eventhandler for adding and connecting lines

class LineTool(BaseTool):
    widget_name = 'Line Tool'
    def __init__(self, obj):
        super(LineTool, self).__init__(obj)

        # get the parametric shape
        _shape = self.parametric_glider.shape.get_half_shape()
        self.ribs = _shape.ribs
        self.front = _shape.front
        self.back = _shape.back
        self.xpos = self.parametric_glider.shape.rib_x_values
        self.disabled_color = (0.5, 0.5, 0.5)

        # setup the GUI
        self.setup_widget()
        self.setup_pivy()


    def setup_pivy(self):        
        # pivy helper line
        self.helper_line = coin.SoSeparator()
        self.temp_point = coin.SoSeparator()

        # pivy lines, points, shape
        self.shape = LineContainer()
        self.shape.selection_changed = self.selection_changed

        self.shape.setName('shape')
        self.shape.register(self.view)
        self.task_separator += [self.shape, self.helper_line]
        self.task_separator += [self.temp_point]
        self.draw_shape()
        self.update_layer_selection()

        self.update_helper_line()
        self.setup_cb()

    def setup_widget(self):
        # qt helper line
        self.Qhl_pos = QtGui.QDoubleSpinBox()

        # qt element widget
        self.tool_widget = QtGui.QStackedWidget()
        self.tool_layout = QtGui.QFormLayout(self.tool_widget)

        # qt layer widget
        self.layer_widget = QtGui.QWidget()
        self.layer_layout = QtGui.QFormLayout(self.layer_widget)
        self.layer_selection = LayerComboBox(self.layer_widget)
        self.layer_combobox = LayerComboBox(self.layer_widget)
        self.layer_color_button = QtGui.QPushButton('select color')
        self.layer_color_dialog = QtGui.QColorDialog()

        self.tool_widget.setWindowTitle('object properties')
        self.layer_widget.setWindowTitle('layers')
        self.form.append(self.layer_widget)
        self.form.append(self.tool_widget)

        # temp_wid = QtGui.QWidget()
        # temp_lay = QtGui.QHBoxLayout(temp_wid)
        # self.layout.setWidget(1, input_field, temp_wid)

        self.none_widget = QtGui.QWidget()
        self.line_widget = QtGui.QWidget()
        self.lw_att_wid = QtGui.QWidget()
        self.up_att_wid = QtGui.QWidget()
        self.Qline_list = QtGui.QListWidget()
        for _type in LineType.types.values():
            self.Qline_list.addItem(QLineType_item(_type))
        self.Qline_list.sortItems()

        self.up_att_lay = QtGui.QFormLayout(self.up_att_wid)
        self.lw_att_lay = QtGui.QFormLayout(self.lw_att_wid)
        self.line_layout = QtGui.QFormLayout(self.line_widget)
        self.none_layout = QtGui.QFormLayout(self.none_widget)

        self.target_length = QtGui.QDoubleSpinBox()
        self.target_length.setDecimals(5)
        self.line_layout.setWidget(
            0, text_field, QtGui.QLabel('target length: '))
        self.line_layout.setWidget(0, input_field, self.target_length)
        self.line_layout.setWidget(1, text_field, QtGui.QLabel('line type: '))
        self.line_layout.setWidget(1, input_field, self.Qline_list)
        self.target_length.valueChanged.connect(self.update_target_length)
        self.Qline_list.currentItemChanged.connect(self.update_line_type)
        self.QLineName = QtGui.QLineEdit()
        self.line_layout.setWidget(2, text_field, QtGui.QLabel('name'))
        self.line_layout.setWidget(2, input_field, self.QLineName)
        self.QLineName.textChanged.connect(self.line_name_changed)

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
        self.up_att_lay.setWidget(0, text_field, QtGui.QLabel('force'))
        self.up_att_lay.setWidget(0, input_field, self.up_att_force)
        self.up_att_force.valueChanged.connect(self.update_up_att_force)

        self.up_att_rib = QtGui.QSpinBox()
        self.up_att_rib.setMinimum(0)
        self.up_att_rib.setMaximum(self.parametric_glider.shape.half_rib_num - 1)
        self.up_att_lay.setWidget(1, text_field, QtGui.QLabel('rib nr'))
        self.up_att_lay.setWidget(1, input_field, self.up_att_rib)
        self.up_att_rib.valueChanged.connect(self.update_up_att_rib)

        self.up_att_pos = QtGui.QDoubleSpinBox()
        self.up_att_pos.setMinimum(0)
        self.up_att_pos.setMaximum(1)
        self.up_att_pos.setSingleStep(0.01)
        self.up_att_lay.setWidget(2, text_field, QtGui.QLabel('position'))
        self.up_att_lay.setWidget(2, input_field, self.up_att_pos)
        self.up_att_pos.valueChanged.connect(self.update_up_att_pos)

        self.tool_widget.addWidget(self.none_widget)
        self.tool_widget.addWidget(self.line_widget)
        self.tool_widget.addWidget(self.lw_att_wid)
        self.tool_widget.addWidget(self.up_att_wid)
        self.tool_widget.setCurrentWidget(self.none_widget)

        button = QtGui.QPushButton('Help')
        self.layout.setWidget(0, input_field, button)
        button.clicked.connect(self.show_help)

        self.Qhl_pos.setValue(50)
        self.Qhl_pos.setRange(0, 100)
        self.Qhl_pos.setSingleStep(1)
        self.Qhl_pos.connect(
            self.Qhl_pos,
            QtCore.SIGNAL('valueChanged(double)'),
            self.update_helper_line)

        self.layout.setWidget(1, text_field, QtGui.QLabel('helper_line_pos'))
        self.layout.setWidget(1, input_field, self.Qhl_pos)

        # layers:

        add_button = QtGui.QPushButton('add layer')
        del_button = QtGui.QPushButton('delete layer')
        self.layer_layout.setWidget(
            0, text_field, QtGui.QLabel('work on layer'))
        self.layer_layout.setWidget(0, input_field, self.layer_combobox)
        self.layer_layout.setWidget(1, text_field, add_button)
        self.layer_layout.setWidget(1, input_field, del_button)
        self.layer_layout.setWidget(2, text_field, QtGui.QLabel('setLayer'))
        self.layer_layout.setWidget(2, input_field, self.layer_selection)
        self.layer_layout.setWidget(3, text_field, QtGui.QLabel('select color of disabled lines'))
        self.layer_layout.setWidget(3, input_field, self.layer_color_button)

        # dialogs
        self.add_layer_dialog = QtGui.QInputDialog()
        add_button.clicked.connect(self.add_new_layer)
        del_button.clicked.connect(self.delete_layer)
        self.layer_combobox.currentIndexChanged.connect(self.show_layer)
        self.layer_selection.activated.connect(self.set_layer_by_current)
        self.layer_selection.setEnabled(False)
        self.layer_color_button.clicked.connect(self.layer_color_dialog.open)
        self.layer_color_dialog.accepted.connect(self.color_changed)

    def color_changed(self):
        color = self.layer_color_dialog.currentColor().getRgbF()[:-1]
        for obj in self.shape.objects:
            obj.disabled_col = color
            if not obj.enabled:
                obj.set_disabled()

    def line_name_changed(self, name):
        self.shape.selected_objects[0].name = name

    def add_new_layer(self):
        self.add_layer_dialog.exec_()
        text = self.add_layer_dialog.textValue()
        self.layer_combobox.addItem(text)
        index = self.layer_combobox.findText(text)
        self.layer_combobox.setCurrentIndex(index)
        self.set_layer(text=text)
        self.show_layer()
        self.update_layer_selection()
        self.layer_combobox.model().sort(0)
        self.layer_selection.model().sort(0)

    def delete_layer(self):
        current_layer = self.layer_combobox.currentText()
        self.set_layer(text='', objects=self.shape.objects,
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
        objects = objects or self.shape.selected_objects
        for obj in objects:
            if hasattr(obj, 'layer'):
                if from_layer is None or from_layer == obj.layer:
                    obj.layer = text

    def show_layer(self):
        self.shape.deselect_all()
        for obj in self.shape.objects:
            if hasattr(obj, 'layer'):
                if self.layer_combobox.currentText() == '':
                    if not obj.enabled:
                        obj.set_enabled()
                elif obj.layer != self.layer_combobox.currentText():
                    if obj.enabled:
                        obj.set_disabled()
                else:
                    if not obj.enabled:
                        obj.set_enabled()

    def show_help(self):
        App.Console.PrintMessage('Use this commands to rule the lineinput\n')
        App.Console.PrintMessage('g...grap element and move it\n')
        App.Console.PrintMessage('l...create line from 2 points\n')
        App.Console.PrintMessage('v...add a new point\n')
        App.Console.PrintMessage('x...delete a point or a line\n')
        App.Console.PrintMessage('cltr + p...attachment point\n')
        App.Console.PrintMessage('cltr...multiselection\n')

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
            self.view.removeEventCallbackPivy(coin.SoKeyboardEvent.getClassTypeId(), self.line_cb)
        if self.node_cb:
            self.view.removeEventCallbackPivy(coin.SoKeyboardEvent.getClassTypeId(), self.node_cb)

    def update_helper_line(self, pos=50):
        self.helper_line.removeAllChildren()
        l = Line(vector3D(self.help_line(pos / 100)), dynamic=False)
        l.set_color('red')
        self.helper_line += [l]

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
                    m.set_color('blue')
                    self.temp_point += [m]
                    break

    def add_line(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord('l') and
            event.getState() == 1):
            objs = self.shape.selected_objects
            if len(objs) == 2:
                if (isinstance(objs[0], NodeMarker) and
                    isinstance(objs[1], NodeMarker)):
                    line = ConnectionLine(objs[0], objs[1])
                    line.layer = self.layer_combobox.currentText()
                    self.shape += [line]
            elif len(objs) == 1:
                if (isinstance(objs[0], NodeMarker)):
                    marker2 = self.node_cb(event_callback, force=True)
                    if marker2:
                        line = ConnectionLine(objs[0], marker2)
                        self.shape += [line]
                        self.shape.Select(marker2)
                        self.shape.selection_changed()
                        line.layer = self.layer_combobox.currentText()

    def add_node(self, event_callback, force=False):
        event = event_callback.getEvent()
        if ((event.getKey() == ord('i') or force) and
            (event.getState() == 1)):
            objs = self.shape.selected_objects
            if len(objs) == 1 and (isinstance(objs[0], Lower_Att_Marker)):
                node = objs[0].node
                point = Lower_Att_Marker(node, self.parametric_glider)
                point.layer = self.layer_combobox.currentText()
                self.shape += [point]
                self.shape.Select(point)
                self.shape.grab_cb(event_callback, force=True)
            elif self.upper_preview_node:
                self.add_attachment_point(self.upper_preview_node[0])
            else:
                pos = event.getPosition()
                pos_3D = list(self.view.getPoint(*pos))
                pos_3D[-1] = 0.
                if event.wasCtrlDown():
                    node = LowerNode2D(pos_3D[:-1], [0, 0, 0])
                    point = Lower_Att_Marker(node, self.parametric_glider)
                    point.layer = self.layer_combobox.currentText()
                else:
                    node = BatchNode2D(pos_3D[:-1])
                    point = NodeMarker(node, self.parametric_glider)
                    point.layer = self.layer_combobox.currentText()
                self.shape += [point]
                return point

    def copy_node(self, event_callback, force=False):
        event = event_callback.getEvent()
        if ((event.getKey() == ord('c')) and
            (event.getState() == 1)):
            # get selection
            objs = self.shape.selected_objects
            if len(objs) == 1 and (isinstance(objs[0], Upper_Att_Marker)):
                node = objs[0].node
                ap = Upper_Att_Marker(node, self.parametric_glider)
                ap.layer = self.layer_combobox.currentText()
                self.shape += [ap]

    def add_attachment_point(self, pos):
        x, y = pos
        rib_nr = self.xpos.index(x)
        pos = float(self.Qhl_pos.value())
        node = UpperNode2D(rib_nr, pos / 100)
        node_pos = node.get_2D(self.parametric_glider.shape)
        ap = Upper_Att_Marker(node, self.parametric_glider)
        ap.layer = self.layer_combobox.currentText()
        self.shape += [ap]

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

        selected_objs = self.shape.selected_objects
        if selected_objs:
            self.layer_selection.setEnabled(True)
            self.target_length.setEnabled(True)
            self.layer_selection.setItemByText(selected_objs[0].layer)
            # self.layer_combobox.blockSignals(True)
            # self.layer_combobox.setItemByText(selected_objs[0].layer)
            # self.layer_combobox.blockSignals(False)
            if show_line_widget(selected_objs):
                self.tool_widget.setCurrentWidget(self.line_widget)
                if has_uppermost_line(selected_objs):
                    self.target_length.setEnabled(False)
                else:
                    self.target_length.setValue(selected_objs[0].target_length)
                line_type_item = self.Qline_list.findItems(
                    selected_objs[0].line_type, QtCore.Qt.MatchExactly)[0]
                self.Qline_list.setCurrentItem(line_type_item)
                if len(selected_objs) != 1:
                    self.QLineName.setDisabled(True)
                else:
                    self.QLineName.blockSignals(True)
                    self.QLineName.setText(selected_objs[0].name)
                    self.QLineName.blockSignals(False)
                    self.QLineName.setEnabled(True)
            elif show_lower_att_widget(selected_objs):
                self.tool_widget.setCurrentWidget(self.lw_att_wid)
                x, y, z = selected_objs[0].pos_3D
                self.attach_x_val.setValue(x)
                self.attach_y_val.setValue(y)
                self.attach_z_val.setValue(z)
            elif show_upper_att_widget(selected_objs):
                self.tool_widget.setCurrentWidget(self.up_att_wid)
                self.up_att_force.setValue(selected_objs[0].force)
                rib_nr = set([i.rib_nr for i in selected_objs])
                if len(rib_nr) > 1:
                    self.up_att_rib.setDisabled(True)
                else:
                    self.up_att_rib.setValue(list(rib_nr)[0])
                    self.up_att_rib.setEnabled(True)
                pos = selected_objs[0].rib_pos
                self.up_att_pos.setValue(pos)
                self.up_att_pos.setEnabled(True)
            else:
                self.tool_widget.setCurrentWidget(self.none_widget)
        else:
            self.tool_widget.setCurrentWidget(self.none_widget)
            self.layer_selection.setEnabled(False)

    def update_target_length(self, *args):
        l = float(self.target_length.value())
        for obj in self.shape.selected_objects:
            obj.target_length = l

    def update_line_type(self, *args):
        for obj in self.shape.selected_objects:
            obj.line_type = self.Qline_list.currentItem().line_type.name

    def update_lw_att_pos(self, *args):
        x = self.attach_x_val.value()
        y = self.attach_y_val.value()
        z = self.attach_z_val.value()
        for obj in self.shape.selected_objects:
            obj.pos_3D = [x, y, z]

    def update_up_att_force(self, *args):
        for obj in self.shape.selected_objects:
            obj.force = self.up_att_force.value()

    def update_up_att_rib(self, *args):
        for obj in self.shape.selected_objects:
            obj.rib_nr = self.up_att_rib.value()

    def update_up_att_pos(self, *args):
        # print('update pos')
        for obj in self.shape.selected_objects:
            obj.rib_pos = self.up_att_pos.value()

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape += [Line(vector3D(self.front)), Line(vector3D(self.back))]
        self.shape += list(map(Line, vector3D(self.ribs)))
        shape = self.parametric_glider.shape
        # make own seperator for shape
        nodes = {}
        for node in self.parametric_glider.lineset.nodes:
            if isinstance(node, UpperNode2D):
                # coord = self.parametric_glider.shape_point(node.rib_no, node.position/100)
                pos = node.get_2D(self.parametric_glider.shape)
                obj = Upper_Att_Marker(node, self.parametric_glider)
                obj.force = node.force
                self.shape += [obj]
            elif isinstance(node, BatchNode2D):
                obj = NodeMarker(node, self.parametric_glider)
                self.shape += [obj]
            elif isinstance(node, LowerNode2D):
                obj = Lower_Att_Marker(node, self.parametric_glider)
                obj.pos_3D = node.pos_3D
                obj._node = node
                self.shape += [obj]
            nodes[node] = obj
            self.layer_combobox.addItem(node.layer)

        for line in self.parametric_glider.lineset.lines:
            m1 = nodes[line.lower_node]
            m2 = nodes[line.upper_node]
            obj = ConnectionLine(m1, m2)
            obj.line_type = line.line_type.name
            obj.target_length = line.target_length
            obj.name = line.name
            obj.layer = line.layer
            self.shape += [obj]
            self.layer_combobox.addItem(line.layer)
        self.layer_combobox.model().sort(0)
        self.layer_selection.model().sort(0)
        self.show_layer()

    def accept(self):
        '''glider 2d will recive the 2d information
            the attachmentpoints are already stored.
            the other points are stored into the batch_points list
        '''
        lines = []

        for obj in self.shape.objects:
            if isinstance(obj, ConnectionLine):
                l = Line2D(obj.marker1.node, obj.marker2.node)
                if not obj.is_uppermost_line():
                    l.target_length = obj.target_length
                l.line_type = LineType.types[obj.line_type]
                l.layer = obj.layer
                l.name = obj.name
                lines.append(l)
                if isinstance(l.upper_node, UpperNode2D):
                    l.upper_node.name = obj.name

        lineset = self.parametric_glider.lineset
        try:
            new_lines = LineSet2D(lines)
            self.parametric_glider.lineset = new_lines
            self.parametric_glider.get_glider_3d(self.obj.Proxy.getGliderInstance())
        except Exception as e:
            App.Console.PrintError(traceback.format_exc())
            self.parametric_glider.lineset = lineset
            self.parametric_glider.get_glider_3d(self.obj.Proxy.getGliderInstance())
            return

        self.shape.unregister()
        self.remove_all_callbacks()
        super(LineTool, self).accept()
        self.update_view_glider()
        
    def reject(self):
        self.shape.unregister()
        self.remove_all_callbacks()
        super(LineTool, self).reject()


class NodeMarker(Marker):
    std_col = 'black'
    ovr_col = 'red'
    sel_col = 'yellow'

    def __init__(self, node, par_glider, pos=None):
        if pos is None:
            pos = node.get_2D(par_glider.shape)
        pos = vector3D(pos)
        super(NodeMarker, self).__init__([pos], dynamic=True)
        self._node = node
        self.par_glider = par_glider

    @property
    def node(self):
        self._node.pos_2D = list(self.pos)[:-1]
        return self._node

    @property
    def pos(self):
        return list(self.points[0])

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
    std_col = 'blue'
    def __init__(self, node, par_glider):
        super(Upper_Att_Marker, self).__init__(node, par_glider)

    @property
    def force(self):
        return self._node.force

    @force.setter
    def force(self, value):
        self._node.force = value

    @property
    def rib_nr(self):
        return self._node.cell_no

    @rib_nr.setter
    def rib_nr(self, nr):
        self._node.cell_no = nr
        self.pos = vector3D(self._node.get_2D(self.par_glider.shape))
        for foo in self.on_drag:
            foo()

    @property
    def rib_pos(self):
        return self._node.rib_pos

    @rib_pos.setter
    def rib_pos(self, pos):
        self._node.rib_pos = pos
        # print('update pos')
        self.pos = vector3D(self._node.get_2D(self.par_glider.shape))
        for foo in self.on_drag:
            foo()

    def drag(self, *arg):
        pass        


class Lower_Att_Marker(NodeMarker):
    std_col = 'green'

    def __init__(self, node, par_glider):
        pos = node.pos_2D
        super(Lower_Att_Marker, self).__init__(node, par_glider)

    @property
    def pos_3D(self):
        return self._node.pos_3D

    @pos_3D.setter
    def pos_3D(self, value):
        self._node.pos_3D = value

    @property
    def pos(self):
        return list(self.points[0])

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
        self.line_type = 'default'
        self.layer = ''
        self.name = 'line_name'

    def is_uppermost_line(self):
        return (isinstance(self.marker1, Upper_Att_Marker) or 
                isinstance(self.marker2, Upper_Att_Marker))

    def update_Line(self):
        self.points = [self.marker1.pos, self.marker2.pos]

    # def drag(self, mouse_coords, fact=1.):
    #     self.marker1.drag(mouse_coords, fact)
    #     self.marker2.drag(mouse_coords, fact)

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
        self.addItem('')

    def addItem(self, text):
        if self.findText(text) == -1:
            super(LayerComboBox, self).addItem(text)

    def removeItem(self, index):
        super(LayerComboBox, self).removeItem(index)
        if self.count() == 0:
            self.addItem('')

    def removeAll(self):
        while self.currentIndex() != -1:
            super(LayerComboBox, self).removeItem(self.currentIndex())

    def getAllItems(self, other):
        self.removeAll()
        for i in range(other.count()):
            self.addItem(other.itemText(i))

    def currentText(self):
        return self.itemText(self.currentIndex())

    def setItemByText(self, text):
        item = self.findText(text)
        if item != -1:
            self.setCurrentIndex(item)


class LineSelectionSeperator(InteractionSeparator):
    def register(self, view, observer_tool):
        self.view = view
        self.observer_tool = observer_tool
        self.mouse_over = self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over_cb)
        self.select = self.view.addEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select_cb)
        self.select_all = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all_cb)

    def unregister(self):
        self.view.removeEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over)
        self.view.removeEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all)

    def selection_changed(self):
        self.observer_tool.selection_changed(*self.get_data())

    def get_data(self):
        line_force = np.zeros(3)
        line_length = np.zeros(3)
        node_force = np.zeros(3)
        for obj in self.selected_objects:
            if isinstance(obj, GliderLine):
                line_force += obj.line.force * obj.line.diff_vector
                line_length[0] += obj.line.length_no_sag
                try:
                    line_length[1] += obj.line.length_with_sag
                    line_length[2] += obj.line.get_stretched_length()
                except ValueError:
                    pass
        return line_force, line_length


class GliderLine(Line):
    def __init__(self, line):
        points = [line.lower_node.vec, line.upper_node.vec]
        points = line.get_line_points(2)
        super(Line, self).__init__(points, dynamic=True)
        self.line = line



class LineObserveTool(BaseTool):
    widget_name = 'line observe tool'
    turn = False
    def __init__(self, obj):
        super(LineObserveTool, self).__init__(obj)
        self.g3d = self.obj.Proxy.getGliderInstance()
        self.setup_qt()
        self.g3d.lineset.recalc(False)
        self.draw_glider()

    def setup_qt(self):
        self.force = QtGui.QLabel("x: {:5.1f} N\n"\
                                  "y: {:5.1f} N\n"\
                                  "z: {:5.1f} N".format(0, 0, 0))
        self.length = QtGui.QLabel("length without sag: {:5.3f} m\n"\
                                   "length with sag:    {:5.3f} m\n"\
                                   "stretched lengths:  {:5.3f} m".format(0, 0, 0))

        self.force_factor = QtGui.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.force_factor.setTickInterval(100)
        self.force_factor.setMinimum(1)
        self.force_factor.setValue(10)

        self.layout.setWidget(0, text_field, QtGui.QLabel("force"))
        self.layout.setWidget(0, input_field, self.force)

        self.layout.setWidget(1, text_field, QtGui.QLabel("length"))
        self.layout.setWidget(1, input_field, self.length)

        self.layout.setWidget(2, text_field, QtGui.QLabel("force-factor"))
        self.layout.setWidget(2, input_field, self.force_factor)


        self.recalc_button = QtGui.QPushButton("recompute")
        self.sag_check = QtGui.QCheckBox("sag")
        self.sag_check.setTristate(False)
        self.sag_check.setCheckState(QtCore.Qt.CheckState(False))
        self.layout.setWidget(3, input_field, self.recalc_button)
        self.layout.setWidget(3, text_field, self.sag_check)


        self.force_factor.sliderReleased.connect(self.draw_residual_forces)
        self.recalc_button.clicked.connect(self.recompute_lines)


    def recompute_lines(self):
        calculate_sag = bool(self.sag_check.checkState())
        self.g3d.lineset.recalc(calculate_sag=calculate_sag)
        self.line_sep.unregister()
        self.task_separator.removeAllChildren()
        self.draw_glider()


    def draw_glider(self):
        _rot = coin.SbRotation()
        _rot.setValue(coin.SbVec3f(0, 1, 0), coin.SbVec3f(1, 0, 0))
        rot = coin.SoRotation()
        rot.rotation.setValue(_rot)
        self.task_separator += rot        
        draw_glider(self.g3d, self.task_separator, profile_num=50, hull=None, ribs=True, fill_ribs=False)
        # self.g3d.lineset.recalc(calculate_sag=True)

        self.line_sep = LineSelectionSeperator()
        self.arrows = coin.SoSeparator()
        self.task_separator += self.line_sep, self.arrows
        for line in self.g3d.lineset.lines:
            self.line_sep += GliderLine(line)
        self.line_sep.register(self.view, self)
        self.draw_residual_forces()

    def draw_residual_forces(self, factor=None):
        self.arrows.removeAllChildren()
        factor = (factor or self.force_factor.value()) * 1e-3
        for node in self.g3d.lineset.nodes:
            if True: #node.type == 1:
                point = node.vec
                force = self.g3d.lineset.get_residual_force(node) * factor
                force *= 1 - 2 * (node.type == 1)
                if np.linalg.norm(force) > 1e-4:
                    arrow = Arrow([point, point - force], arrow_size=0.05 * np.linalg.norm(force))
                    arrow.set_color("red")
                    self.arrows += arrow

    def selection_changed(self, force, length):
        self.force.setText("x: {:5.1f} N\n"\
                           "y: {:5.1f} N\n"\
                           "z: {:5.1f} N".format(*force))
        self.length.setText("length without sag: {:5.3f} m\n"\
                            "length with sag:    {:5.3f} m\n"\
                            "stretched lengths   {:5.3f} m".format(*length))

    def accept(self):
        self.line_sep.unregister()
        super(LineObserveTool, self).accept()

    def reject(self):
        self.line_sep.unregister()
        super(LineObserveTool, self).reject()