from __future__ import division

from copy import deepcopy
import euklid
import numpy as np
from pivy import coin
from pivy.graphics import InteractionSeparator, Marker, Line

import FreeCAD
import FreeCADGui
import openglider
from openglider.glider import ParametricGlider
from openglider.jsonify import dump, load
from PySide import QtGui



class ConstrainedMarker(Marker):
    def __init__(self, points, dynamic=False):
        super(ConstrainedMarker, self).__init__(points, dynamic)
        self.constrained = [1., 1., 0.]

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, pt in enumerate(pts):
                pt[0] = mouse_coords[0] * fact * self.constrained[0] + self._tmp_points[i][0]
                pt[1] = mouse_coords[1] * fact * self.constrained[1] + self._tmp_points[i][1]
                pt[2] = mouse_coords[2] * fact * self.constrained[2] + self._tmp_points[i][2]
            self.points = pts
            for foo in self.on_drag:
                foo()


class Line_old(object):
    def __init__(self, points, color='black', width=1):
        if len(points) == 0:
            points = [[0., 0., 0.]]
        self.object = Line(list(map(vector3D, points)))
        self.object.drawstyle.lineWidth = width
        self.object.set_color(color)

    def update(self, points):
        self.object.points = vector3D(points)

class ControlPointContainer(coin.SoSeparator):
    def __init__(self, rm, points=None):
        super(ControlPointContainer, self).__init__()
        self.interaction = InteractionSeparator(rm)
        self.control_points = []
        if points is not None:
            self.control_pos = points
        self += self.interaction
        self.on_drag_release = self.interaction.on_drag_release
        self.drag_release = self.on_drag_release
        self.on_drag = self.interaction.on_drag
        self.remove_callbacks = self.interaction.unregister
        self.interaction.remove_selected = self.pseudo_foo
        self.interaction.register()

    def pseudo_foo(*args):
        pass

    @property
    def control_pos(self):
        return [list(i.points[0]) for i in self.control_points]

    @control_pos.setter
    def control_pos(self, points):
        controlpoints = vector3D(points)
        self.control_points = [ConstrainedMarker([point], dynamic=True) for point in controlpoints]

        self.interaction.objects.removeAllChildren()
        self.interaction.dynamic_objects = []
        self.interaction += self.control_points

def vector3D(vec, z=0):
    if len(vec) == 0:
        return(vec)
    elif isinstance(vec, euklid.vector.PolyLine3D):
        return vec.tolist()
    elif isinstance(vec, euklid.vector.PolyLine2D):
        return [p + [z] for p in vec.tolist()]
    elif not isinstance(vec[0], (list, tuple, np.ndarray, FreeCAD.Vector)):
        if len(vec) == 3:
            return list(vec)
        elif len(vec) == 2:
            z = z or 0.
            return np.array(vec).tolist() + [z]
        else:
            print('something wrong with this list: ', vec)
    else:
        return [vector3D(i, z) for i in vec]

def vector2D(vec):
    return vec[0:2]

def hex_to_rgb(hex_string):
    try:
        split = hex_string.split('#')
        if len(split) > 1:
            prefix, value = split
        else:
            value = split
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) / 256. for i in range(0, lv, lv // 3))
    except (IndexError, ValueError) as e:
        return (.7, .7, .7)

def rgb_to_hex(color_tuple, prefix=None):
    assert(all(0 <= i <= 1 for i in color_tuple))
    c = tuple(int(i * 255) for i in color_tuple)
    hex_c = '#%02x%02x%02x' % c
    if prefix:
        hex_c = prefix + hex_c
    return hex_c


def refresh():
    pass

text_field = QtGui.QFormLayout.LabelRole
input_field = QtGui.QFormLayout.FieldRole


def export_glider(glider_2d, glider_3d):
    file_types = "OpenOffice *.ods;;JSON 2d *.json;;JSON 3d *.json"
    filename = QtGui.QFileDialog.getSaveFileName(
        parent=None,
        caption='export glider',
        directory='~',
        filter=file_types)
    if filename[0] != "":
        ext = filename[1].split(".")[-1]
        name = filename[0]
        if not name.endswith(".json") and not name.endswith(".ods"):
            name = name + "." + ext
        if name.endswith(".json"):
            if "3d" in filename[1]:
                print(name)
                print(glider_3d)
                openglider.save(glider_3d, name)
            elif "2d" in filename[1]:
                openglider.save(glider_2d, name)
        if name.endswith(".ods"):
            glider_2d.export_ods(name)


def import_2d(glider):
    filename = QtGui.QFileDialog.getOpenFileName(
        parent=None,
        caption='import glider',
        directory='~')
    if filename[0].endswith('.json'):
        with open(filename, 'r') as importfile:
            glider.ParametricGlider = load(importfile)['data']
            glider.ParametricGlider.get_glider_3d(glider.GliderInstance)
            glider.ViewObject.Proxy.updateData()
    elif filename.endswith('ods'):
        glider.ParametricGlider = ParametricGlider.import_ods(filename)
        glider.ParametricGlider.get_glider_3d(glider.GliderInstance)
        glider.ViewObject.Proxy.updateData()
    else:
        FreeCAD.Console.PrintError('\nonly .ods and .json are supported')

import euklid
class spline_select(QtGui.QComboBox):
    spline_types = {
        'Bezier': (euklid.spline.BezierCurve, 0),
        'BSpline': (euklid.spline.BSplineCurve, 1),
        'BSpline_2': (euklid.spline.BSplineCurve, 2),
        'BSpline_3': (euklid.spline.BSplineCurve, 3)
    }

    def __init__(self, spline_objects, update_function, parent=None):
        super(spline_select, self).__init__(parent)
        self.update_function = update_function
        self.spline_objects = spline_objects    # list of splines
        for key in ['Bezier', 'BSpline_2', 'BSpline_3']:
            self.addItem(key)
        self.setCurrentIndex(self.spline_types[self.current_spline_type][1])
        self.currentIndexChanged.connect(self.set_spline_type)

    @property
    def current_spline_type(self):
        if self.spline_objects:
            spline_obj = self.spline_objects[0]
            if spline_obj.__class__ in (euklid.spline.SymmetricBezierCurve, euklid.spline.BezierCurve):
                return "Bezier"
            else:
                return "BSpline"
        
        return "BSpline"

    def set_spline_type(self, *args):
        spline_type = self.spline_types[self.currentText()][0]
        self.spline_objects = [
            spline_type(spline.controlpoints) for spline in self.spline_objects
        ]
        self.update_function()


class BaseTool(object):
    hide = True
    widget_name = 'Unnamed'
    turn = True

    def __init__(self, obj):
        self.obj = obj
        self.parametric_glider = deepcopy(self.obj.Proxy.getParametricGlider())
        self._vis_object = []
        for obj in FreeCAD.ActiveDocument.Objects:
            try:
                if obj.ViewObject.Visibility:
                    obj.ViewObject.Visibility = False
                    self._vis_object += [obj]
            except Exception:
                pass
        self.obj.ViewObject.Visibility = not self.hide
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.rm = self.view.getViewer().getSoRenderManager()
        FreeCADGui.Selection.clearSelection()
        if self.turn:
            self.view.viewTop()

        # disable the rotation function
        # first get the widget where the scene lives in

        # form is the widget that appears in the task panel
        self.form = []

        self.base_widget = QtGui.QWidget()
        self.form.append(self.base_widget)
        self.layout = QtGui.QFormLayout(self.base_widget)
        self.base_widget.setWindowTitle(self.widget_name)

        # scene container
        self.task_separator = coin.SoSeparator()
        self.task_separator.setName('task_seperator')
        self.scene.addChild(self.task_separator)

    def update_view_glider(self):  # rename
        # 1: update parametric-glider and get the glider_instance
        self.obj.Proxy.setParametricGlider(self.parametric_glider)
        # 2: draw the glider for all visible objects
        self.obj.Proxy.drawGlider()

    def accept(self):
        for obj in self._vis_object:
            obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        FreeCADGui.Control.closeDialog()

    def reject(self):
        for obj in self._vis_object:
            obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        FreeCADGui.Control.closeDialog()

    def setup_widget(self):
        pass

    def setup_pivy(self):
        pass

    @property
    def scene(self):
        return self.view.getSceneGraph()

    @property
    def nav_bak(self):
        return self.view.getNavigationType()
