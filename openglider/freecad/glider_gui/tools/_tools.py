from __future__ import division

from copy import deepcopy

from PySide import QtGui
from pivy import coin
import FreeCADGui as Gui
from openglider.jsonify import dump, load
from openglider.vector.spline import BernsteinBase, BSplineBase

# from openglider.glider.glider_2d import Glider2D


text_field = QtGui.QFormLayout.LabelRole
input_field = QtGui.QFormLayout.FieldRole

# TODO:
#   -merge-tool
#       -airfoil
#       -ballooning
#       -aoa                xx
#       -zrot
#   -airfoil-tool
#   -ballooning-tool
#   -attachmentpoint-tool
#   -line-tool
#   -inlet-tool
#   -design-tool
#   -minirips-tool
#   -etc...


def export_2d(glider):
    filename = QtGui.QFileDialog.getSaveFileName(
        parent=None,
        caption="export glider",
        directory='~')
    if filename[0] != "":
        with open(filename[0], 'w') as exportfile:
            dump(glider.glider_2d, exportfile)


def import_2d(glider):
    filename = QtGui.QFileDialog.getOpenFileName(
        parent=None,
        caption="import glider",
        directory='~')
    if filename[0] != "":
        with open(filename[0], 'r') as importfile:
            glider.glider_2d = load(importfile)["data"]
            glider.glider_2d.get_glider_3d(glider.glider_instance)
            glider.ViewObject.Proxy.updateData()


class spline_select(QtGui.QComboBox):
    spline_types = {
        "Bezier": (BernsteinBase, 0),
        "BSpline_2": (BSplineBase(2), 1),
        "BSpline_3": (BSplineBase(3), 2)
    }

    def __init__(self, spline_objects, update_function, parent=None):
        super(spline_select, self).__init__(parent)
        self.update_function = update_function
        self.spline_objects = spline_objects    # list of splines
        for key in ["Bezier", "BSpline_2", "BSpline_3"]:
            self.addItem(key)
        self.setCurrentIndex(self.spline_types[self.current_spline_type][1])
        self.currentIndexChanged.connect(self.set_spline_type)

    @property
    def current_spline_type(self):
        base = self.spline_objects[0].basefactory
        print(base.__class__)
        if base.__class__ == BernsteinBase.__class__:
            return "Bezier"
        else:
            return "BSpline_" + str(base.degree)

    def set_spline_type(self, *args):
        for spline in self.spline_objects:
            spline.basefactory = self.spline_types[self.currentText()][0]
        self.update_function()


class base_tool(object):
    def __init__(self, obj, widget_name="base_widget", hide=True):
        self.obj = obj
        self.glider_2d = deepcopy(self.obj.glider_2d)
        self.obj.ViewObject.Visibility = not hide
        self.view = Gui.ActiveDocument.ActiveView
        self.view.viewTop()

        # self.view.setNavigationType('Gui::TouchpadNavigationStyle')
        # disable the rotation function
        # first get the widget where the scene ives in

        # form is the widget that appears in the task panel
        self.form = []

        self.base_widget = QtGui.QWidget()
        self.form.append(self.base_widget)
        self.layout = QtGui.QFormLayout(self.base_widget)
        self.base_widget.setWindowTitle(widget_name)

        # scene container
        self.task_separator = coin.SoSeparator()
        self.task_separator.setName("task_seperator")
        self.scene.addChild(self.task_separator)

    def update_view_glider(self):
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.get_glider_3d(self.obj.glider_instance)

    def accept(self):
        self.obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()
        self.view.setNavigationType(self.nav_bak)

    def reject(self):
        self.obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()
        self.view.setNavigationType(self.nav_bak)

    def setup_widget(self):
        pass

    def add_pivy(self):
        pass

    @property
    def scene(self):
        return self.view.getSceneGraph()

    @property
    def nav_bak(self):
        return self.view.getNavigationType()
