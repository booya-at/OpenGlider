from __future__ import division

import numpy as np

import FreeCAD as App
from openglider.glider.cell.elements import Panel
from PySide import QtCore, QtGui

from .tools import BaseTool, coin, input_field, text_field, vector3D
from pivy.graphics import InteractionSeparator, Line, Marker


def refresh():
    pass


# idea: draw lines between ribs and fill the panels with color
# only straight lines, no curves
# later create some helpers to generate parametric cuts

# TODO

# switch upper lower        x
# add new line              x
# add new point             x
# create line of two nodes  x
# save to dict              x
# set cut type              x
# q set position            x
# delete                    x


class DesignTool(BaseTool):
    widget_name = 'Design Tool'
    def __init__(self, obj):
        super(DesignTool, self).__init__(obj)
        self.side = 'upper'

        # get 2d shape properties
        _shape = self.parametric_glider.shape.get_shape()
        self.front = list(map(vector3D, _shape.front))
        self.back = list(map(vector3D, _shape.back))
        self.ribs = zip(self.front, self.back)
        self.x_values = self.parametric_glider.shape.rib_x_values
        CutLine.cuts_to_lines(self.parametric_glider)

        self._add_mode = False
        # setup the GUI
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        '''set up the qt stuff'''
        self.Qtoggle_side = QtGui.QPushButton('show lower side')
        self.layout.setWidget(0, input_field, self.Qtoggle_side)

        self.tool_widget = QtGui.QWidget()
        self.tool_widget.setWindowTitle('object properties')
        self.tool_layout = QtGui.QFormLayout(self.tool_widget)
        self.form.append(self.tool_widget)

        self.Qcut_type = QtGui.QComboBox(self.tool_widget)
        for _, cut_type in Panel.CUT_TYPES():
            self.Qcut_type.addItem(cut_type)
        self.Qcut_type.setEnabled(False)
        self.Qcut_type.currentIndexChanged.connect(self.cut_type_changed)

        self.tool_layout.setWidget(0, text_field, QtGui.QLabel('cut type'))
        self.tool_layout.setWidget(0, input_field, self.Qcut_type)

        self.QPointPos = QtGui.QDoubleSpinBox()
        self.QPointPos.setMinimum(0)
        self.QPointPos.setMaximum(1)
        self.QPointPos.setSingleStep(0.01)
        self.QPointPos.setDecimals(5)
        self.QPointPos.valueChanged.connect(self.point_pos_changed)

        self.tool_layout.setWidget(1, text_field, QtGui.QLabel('point position'))
        self.tool_layout.setWidget(1, input_field, self.QPointPos)


        # event handlers
        self.Qtoggle_side.clicked.connect(self.toggle_side)

    def setup_pivy(self):
        '''set up the scene'''
        self.shape = coin.SoSeparator()
        self.task_separator += [self.shape]
        self.add_separator = InteractionSeparator(self.rm)
        self.shape += [self.add_separator]
        self.draw_shape()
        self.event_separator = InteractionSeparator(self.rm)
        self.event_separator.selection_changed = self.selection_changed
        self.event_separator.register()
        self.toggle_side()
        self.add_cb = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.add_geo)

    def selection_changed(self):
        points = set()
        lines = []
        for element in self.event_separator.selected_objects:
            if isinstance(element, CutPoint):
                points.add(element)
            elif isinstance(element, CutLine):
                lines.append(element)
                points.add(element.point1)
                points.add(element.point2)

        self.Qcut_type.setEnabled(bool(lines))
        self.QPointPos.setEnabled(bool(points))
        if lines:
            self.set_cut_type(lines[0].cut_type)
        if points:
            self.QPointPos.blockSignals(True)
            self.QPointPos.setValue(abs(list(points)[0].rib_pos))  # maybe summing over all points?
            self.QPointPos.blockSignals(False)

    def set_cut_type(self, text):
        index = self.Qcut_type.findText(text)
        if index is not None:
            self.Qcut_type.setCurrentIndex(index)


    def cut_type_changed(self):
        for element in self.event_separator.selected_objects:
            if isinstance(element, CutLine):
                element.cut_type = self.Qcut_type.currentText()

    def point_pos_changed(self):
        points = set()
        lines = set()
        sign = 2. * (self.side != 'upper') - 1.
        for element in self.event_separator.selected_objects:
            if isinstance(element, CutPoint):
                points.add(element)
            elif isinstance(element, CutLine):
                lines.add(element)
                points.add(element.point1)
                points.add(element.point2)
        for point in points:
            point.rib_pos = self.QPointPos.value() * sign
            point.update_position()
            for line in point.lines:
                lines.add(line)
        for line in lines:
            line.update_Line()

    def draw_shape(self):
        ''' draws the shape of the glider'''
        self.shape += [Line(self.front)]
        self.shape += [Line(self.back)]
        self.shape += [Line([self.back[0], self.front[0]])]
        self.shape += [Line([self.back[-1], self.front[-1]])]
        self.shape += list(map(Line, self.ribs))

    def toggle_side(self):
        self.event_separator.select_object(None)
        self.event_separator.unregister()
        self.task_separator.removeChild(self.event_separator)
        del self.event_separator
        self.event_separator = InteractionSeparator(self.rm)
        self.event_separator.selection_changed = self.selection_changed
        if self.side == 'upper':
            self.side = 'lower'
            self.Qtoggle_side.setText('show upper side')
            self.event_separator += list(CutLine.lower_point_set)
            self.event_separator += CutLine.lower_line_list
        elif self.side == 'lower':
            self.side = 'upper'
            self.Qtoggle_side.setText('show lower side')
            self.event_separator += list(CutLine.upper_point_set)
            self.event_separator += CutLine.upper_line_list
        self.task_separator += [self.event_separator]
        self.event_separator.register()

    def add_geo(self, event_callback):
        '''this function provides some interaction functionality to create points and lines
           press v to start the mode. if a point is selected, the left and right rib will offer the possebility to add
           a point + line, if no point is selected, it's possible to add a point to any rib'''
        event = event_callback.getEvent()
        if (event.getKey() == ord('i') and event.getState() == 0):
            if self._add_mode: return
            print(1)
            self._add_mode = True
            # first we check if nothing is selected:
            select_obj = self.event_separator.selected_objects
            num_of_obj = len(select_obj)
            action = None
            add_event = None
            close_event = None

            # insert a point
            if num_of_obj == 0:
                add_event = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.add_point)
                action = self.add_point
                print(2)

            # insert a line + point
            elif num_of_obj == 1 and isinstance(select_obj[0], CutPoint):
                add_event = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.add_neighbour)
                self.add_neighbour(event_callback)
                action = self.add_neighbour

            # join two points with a line
            # add-line
            elif num_of_obj == 2 and all(isinstance(el, CutPoint) for el in select_obj):
                cut_point_1 = select_obj[0]
                cut_point_2 = select_obj[1]
                if abs(cut_point_1.rib_nr - cut_point_2.rib_nr) == 1:
                    cut_line = CutLine(cut_point_1, cut_point_2, 'folded')
                    cut_line.replace_points_by_set()
                    cut_line.update_Line()
                    cut_line.setup_visuals()
                    self.event_separator += [cut_line]
 

            def remove_cb(event_callback=None):
                if event_callback:
                    event = event_callback.getEvent()
                    if not event.getButton() == coin.SoMouseButtonEvent.BUTTON1:
                        return
                if add_event:
                    self.view.removeEventCallbackPivy(
                        coin.SoLocation2Event.getClassTypeId(), add_event)
                if close_event:
                    self.view.removeEventCallbackPivy(
                        coin.SoMouseButtonEvent.getClassTypeId(), close_event)

                if action == self.add_neighbour:
                    assert(len(self.add_separator.static_objects) == 2)
                    assert(isinstance(self.add_separator.static_objects[0], Marker))
                    assert(isinstance(self.add_separator.static_objects[1], Line))
                    marker = self.add_separator.static_objects[0]
                    line = self.add_separator.static_objects[1]
                    cut_point_1 = CutPoint.from_position_and_rib(marker.rib_nr, marker.points[0][1], self.side == 'upper', self.parametric_glider)
                    cut_point_2 = line.active_point
                    cut_line = CutLine(cut_point_1, cut_point_2, 'folded')
                    cut_line.replace_points_by_set()
                    cut_line.update_Line()
                    cut_line.setup_visuals()
                    self.event_separator += [cut_point_1, cut_line]
                    self.event_separator.select_object(cut_point_1)

                elif action == self.add_point:
                    assert(len(self.add_separator.static_objects) == 1)
                    assert(isinstance(self.add_separator.static_objects[0], Marker))
                    marker = self.add_separator.static_objects[0]
                    cut_point = CutPoint.from_position_and_rib(marker.rib_nr, marker.points[0][1], self.side == 'upper', self.parametric_glider)
                    self.event_separator += [cut_point]
                    self.event_separator.select_object(cut_point)


                self._add_mode = False
                self.add_separator.removeAllChildren()

            if action in [self.add_neighbour, self.add_point]:
                # these functions need an extra callback for closing on
                # mouse button press
                close_event = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), remove_cb)
            else: # add line: call remove_callback directly
                remove_cb()

    def add_point(self, event_callback=None):
        event = event_callback.getEvent()
        # first get the closest rib
        pos = event.getPosition()
        pos = list(self.view.getPoint(*pos))
        pos[2] = 0.
        smallest_diff = None, None

        for index, value in enumerate(self.x_values):
            diff = abs(pos[0] - value)
            if (not smallest_diff[0]) or smallest_diff[0] > diff:
                smallest_diff = diff, index
        index = smallest_diff[1]
        x, min_y = self.parametric_glider.shape[index, 1.]
        _, max_y = self.parametric_glider.shape[index, 0.]
        pos[0] = x
        if pos[1] > min_y and pos[1] < max_y:
            if len(self.add_separator.static_objects) == 0:
                self.add_separator.removeAllChildren()
                marker = Marker([pos])
                marker.rib_nr = index
                self.add_separator += [marker]
            else:
                marker = self.add_separator.static_objects[0]
                marker.points = [pos]
                marker.rib_nr = index
        else:
            self.add_separator.removeAllChildren()


    def add_neighbour(self, event_callback=None):
        event = event_callback.getEvent()
        select_obj = self.event_separator.selected_objects[0]
        rib_nr = select_obj.rib_nr
        try:
            min1 = self.parametric_glider.shape[rib_nr - 1, 1.][1]
            x1, max1 = self.parametric_glider.shape[rib_nr - 1, 0.]
        except IndexError:
            min1, x1, max1 = None, None, None
        try:
            min2 = self.parametric_glider.shape[rib_nr + 1, 1.][1]
            x2, max2 = self.parametric_glider.shape[rib_nr + 1, 0.]
        except IndexError:
            min2, x2, max2 = None, None, None
        show_point = False
        pos = event.getPosition()
        pos = list(self.view.getPoint(*pos))
        pos[2] = 0
        if not x2 or abs(pos[0] - x1) < abs(pos[0] - x2):
            pos[0] = x1
            if pos[1] > min1 and pos[1] < max1:
                new_rib_nr = rib_nr - 1
                show_point = True
        elif not x1 or abs(pos[0] - x1) > abs(pos[0] - x2):
            pos[0] = x2
            if pos[1] > min2 and pos[1] < max2:
                new_rib_nr = rib_nr + 1
                show_point = True
        else:
            return
        if show_point:
            if not self.add_separator.static_objects:
                self.add_separator.removeAllChildren()
                marker = Marker([pos])
                marker.rib_nr = new_rib_nr
                line = Line([list(select_obj.points[0]), pos])
                line.active_point = select_obj
                self.add_separator += [marker]
                self.add_separator += [line]
            else:
                marker = self.add_separator.static_objects[0]
                line = self.add_separator.static_objects[1]
                marker.points = [pos]
                marker.rib_nr = new_rib_nr
                line.points = [list(select_obj.points[0]), pos]
        else:
            self.add_separator.removeAllChildren()

    def accept(self):
        self.event_separator.unregister()
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.add_cb)
        self.parametric_glider.elements['cuts'] = CutLine.get_cut_dict()
        super(DesignTool, self).accept()
        self.update_view_glider()

    def reject(self):
        self.event_separator.unregister()
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.add_cb)
        super(DesignTool, self).reject()



class CutPoint(Marker):
    def __init__(self, rib_nr, rib_pos, parametric_glider=None):
        super(CutPoint, self).__init__([[0, 0, 0]], True)
        self.marker.markerIndex = coin.SoMarkerSet.CROSS_7_7
        self.parametric_glider = parametric_glider
        self.rib_nr = rib_nr - parametric_glider.shape.has_center_cell
        self.rib_pos = rib_pos
        self.lines = []
        point = self.get_2D()
        self.x_value = point[0]
        self.max= self.parametric_glider.shape[self.rib_nr, 1.][1]
        self.min= self.parametric_glider.shape[self.rib_nr, 0.][1]
        self.points = [point]
        self.on_drag_release.append(self.get_rib_pos)

    def update_position(self):
        self.points = [self.get_2D()]

    def get_2D(self):
        try:
            return list(self.parametric_glider.shape[self.rib_nr, abs(self.rib_pos)] + [0])
        except IndexError:
            raise IndexError('index ' + self.rib_nr + ' out of range')

    def get_rib_pos(self):
        # we have to do this 
        le = self.parametric_glider.shape[self.rib_nr, 0][1]
        te = self.parametric_glider.shape[self.rib_nr, 1][1]
        chord = le - te
        sign = ((self.rib_pos >= 0) * 2 - 1)
        self.rib_pos = round(sign * (abs(le - self.pos[1])) / chord, 3)
        return self.rib_pos

    def __eq__(self, other):
        if isinstance(other, CutPoint):
            if self.rib_nr == other.rib_nr:
                if round(self.rib_pos, 3) == round(other.rib_pos, 3):
                    return True
        return False

    def __hash__(self):
        return (hash(self.rib_nr) ^ hash(round(self.rib_pos, 2)))
        
    def replace_by_set(self, point_set):
        for point in point_set:
            if point == self:
                return point
        return False

    @property
    def pos(self):
        return [self.x_value, self.points[0][1], 0]

    @pos.setter
    def pos(self, pos):
        self.points = [self.x_value, pos[1], 0]

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, pt in enumerate(pts):
                pt[0] = self._tmp_points[i][0]
                y = mouse_coords[1] * fact + self._tmp_points[i][1]
                if y > self.min:
                    pt[1] = self.min
                elif y < self.max:
                    pt[1] = self.max
                else:
                    pt[1] = y
                pt[2] = self._tmp_points[i][2]
            self.points = pts
            for i in self.on_drag:
                i()

    @classmethod
    def from_position_and_rib(cls, rib_nr, y_pos, upper, parametric_glider):
        i = 0
        max_val = parametric_glider.shape[rib_nr, 1.][1]
        min_val = parametric_glider.shape[rib_nr, 0.][1]
        rib_pos = -(upper * 2. - 1.) * abs(y_pos - min_val) / abs(max_val - min_val) 
        return cls(rib_nr + parametric_glider.shape.has_center_cell, rib_pos, parametric_glider)


class CutLine(Line):
    upper_point_set = set()
    lower_point_set = set()
    upper_line_list = []
    lower_line_list = []
    def __init__(self, point1, point2, cut_type):
        super(CutLine, self).__init__([point1.get_2D(), point2.get_2D()], dynamic=True)
        self.point1 = point1
        self.point2 = point2
        self.parametric_glider = self.point1.parametric_glider
        self.cut_type = cut_type
        if self.is_upper:
            CutLine.upper_point_set.add(point1)
            CutLine.upper_point_set.add(point2)
            CutLine.upper_line_list.append(self)
        else:
            CutLine.lower_point_set.add(point1)
            CutLine.lower_point_set.add(point2)
            CutLine.lower_line_list.append(self)

    def setup_visuals(self):
        self.point1.lines.append(self)
        self.point2.lines.append(self)
        self.point1.on_drag.append(self.update_Line)
        self.point2.on_drag.append(self.update_Line)
        
    def replace_points_by_set(self):
        # this has to be done once for every line (before the parent Line is initialized)
        if self.is_upper:
            self.point1 = self.point1.replace_by_set(CutLine.upper_point_set)
            self.point2 = self.point2.replace_by_set(CutLine.upper_point_set)
        else:
            self.point1 = self.point1.replace_by_set(CutLine.lower_point_set)
            self.point2 = self.point2.replace_by_set(CutLine.lower_point_set)

    def update_Line(self):
        self.points = [self.point1.pos, self.point2.pos]

    @property
    def is_upper(self):
        return self.point1.rib_pos < 0 and self.point2.rib_pos < 0

    def drag(self, mouse_coords, fact=1.):
        self.point1.drag(mouse_coords, fact)
        self.point2.drag(mouse_coords, fact)

    @property
    def drag_objects(self):
        return [self.point1, self.point2]

    @property
    def points(self):
        return self.data.point.getValues()

    @points.setter
    def points(self, points):
        p = [[pi[0], pi[1], pi[2] - 0.001] for pi in points]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)

    @classmethod
    def cuts_to_lines(cls, parametric_glider):
        CutLine.upper_point_set = set()
        CutLine.lower_point_set = set()
        CutLine.upper_line_list = []
        CutLine.lower_line_list = []
        for cut in parametric_glider.elements['cuts']:
            for cell_nr in cut['cells']:
                    try:
                        CutLine(CutPoint(cell_nr, cut['left'], parametric_glider), 
                                CutPoint(cell_nr + 1, cut['right'], parametric_glider),
                                cut['type'])
                    except TypeError:
                        # hack if cell_nr out of range
                        pass
        for l in cls.upper_line_list:
            l.replace_points_by_set()
            l.setup_visuals()
        for l in cls.lower_line_list:
            l.replace_points_by_set()
            l.setup_visuals()

    @property
    def cell_nr(self):
        return self.get_point(inner=True).rib_nr + self.point1.parametric_glider.shape.has_center_cell

    def get_point(self, inner=True):
        if (self.point1.rib_nr < self.point2.rib_nr) == inner:
            return self.point1
        else:
            return self.point2

    def get_dict(self):
        return {
            'cells': [self.cell_nr],
            'left': self.get_point(inner=True).get_rib_pos(),
            'right' : self.get_point(inner=False).get_rib_pos(),
            'type' : self.cut_type
        }

    @classmethod
    def get_cut_dict(cls):
        cuts = [line.get_dict() for line in cls.upper_line_list + cls.lower_line_list]
        cuts = sorted(cuts, key=lambda x: x['right'])
        if not cuts:
            return []
        sorted_cuts = [cuts[0]]
        for cut in cuts[1:]:
            for key in ['type', 'left', 'right']:
                if cut[key] != sorted_cuts[-1][key]:
                    sorted_cuts.append(cut)
                    break
            else:
                sorted_cuts[-1]['cells'].append(cut['cells'][0])
        return sorted_cuts

    def check_dependency(self):
        if (not self._delete) and (self.point1._delete or self.point2._delete):
            self.delete()

    def delete(self):
        if self.is_upper:
            CutLine.upper_line_list.remove(self)
        else:
            CutLine.lower_line_list.remove(self)
        super(CutLine, self).delete()
