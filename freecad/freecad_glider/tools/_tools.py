from __future__ import division

from copy import deepcopy
import FreeCAD

from PySide import QtGui
from pivy import coin
import FreeCADGui as Gui
import FreeCAD as App
import openglider
from openglider.jsonify import dump, load
from openglider.vector.spline import BernsteinBase, BSplineBase
from openglider.glider import ParametricGlider


def hex_to_rgb(hex_string):
    try:
        value = hex_string.split('#')[1]
        lv = len(value)
        return tuple(int(value[i:i + lv // 3], 16) / 256. for i in range(0, lv, lv // 3))
    except IndexError:
        return (.7, .7, .7)

def rgb_to_hex(color_tuple):
    assert(all(0 <= i <= 1 for i in color_tuple))
    c = tuple(int(i * 255) for i in color_tuple)
    return '#%02x%02x%02x' % c


def refresh():
    pass

text_field = QtGui.QFormLayout.LabelRole
input_field = QtGui.QFormLayout.FieldRole


def export_2d(glider):
    file_types = "OpenOffice *.ods;;JSON 2d *.json;;JSON 3d *.json"
    filename = QtGui.QFileDialog.getSaveFileName(
        parent=None,
        caption='export glider',
        directory='~',
        filter=file_types)
    if hasattr(glider.Proxy, "getParametricGlider"):
        glider_2d = glider.Proxy.getParametricGlider()
        glider_3d = glider.Proxy.getGliderInstance()
    else:
        glider_2d = glider.ParametricGlider
        glider_3d = glider.GliderInstance
    if filename[0] != "":
        ext = filename[1].split(".")[-1]
        name = filename[0]
        name = name + "." + ext
        if ext == ".json":
            if "3d" in filename[1]:
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


class spline_select(QtGui.QComboBox):
    spline_types = {
        'Bezier': (BernsteinBase, 0),
        'BSpline_2': (BSplineBase(2), 1),
        'BSpline_3': (BSplineBase(3), 2)
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
            base = self.spline_objects[0].basefactory
            if base.__class__ == BernsteinBase.__class__:
                return 'Bezier'
            else:
                return 'BSpline_' + str(base.degree)
        else:
            return 'Bezier'

    def set_spline_type(self, *args):
        for spline in self.spline_objects:
            spline.change_base(self.spline_types[self.currentText()][0])
        self.update_function()


class BaseTool(object):
    hide = True
    widget_name = 'Unnamed'
    turn = True

    def __init__(self, obj):
        self.obj = obj
        self.parametric_glider = deepcopy(self.obj.Proxy.getParametricGlider())
        self._vis_object = []
        for obj in App.ActiveDocument.Objects:
            try:
                if obj.ViewObject.Visibility:
                    obj.ViewObject.Visibility = False
                    self._vis_object += [obj]
            except Exception:
                pass
        self.obj.ViewObject.Visibility = not self.hide
        self.view = Gui.ActiveDocument.ActiveView
        Gui.Selection.clearSelection()
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
        Gui.Control.closeDialog()

    def reject(self):
        for obj in self._vis_object:
            obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()

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
