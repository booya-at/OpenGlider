import numpy
from pivy import coin
from PySide import QtGui

import FreeCADGui as Gui

from openglider.airfoil import BezierProfile2D
from openglider.vector import normalize, norm
from _tools import base_tool
from pivy_primitives import Line, vector3D, ControlPointContainer


class airfoil_tool(base_tool):

    def __init__(self, obj):
        super(airfoil_tool, self).__init__(obj, widget_name="selection")
        # base_widget
        self.QList_View = QtGui.QListWidget(self.base_widget)
        self.Qdelete_button = QtGui.QPushButton("delete", self.base_widget)
        self.Qnew_button = QtGui.QPushButton("new", self.base_widget)
        self.Qairfoil_name = QtGui.QLineEdit()

        self.Qairfoil_widget = QtGui.QWidget()
        self.Qairfoil_layout = QtGui.QFormLayout(self.Qairfoil_widget)
        self.Qimport_button = QtGui.QPushButton("import airfoil")
        self.Qfit_button = QtGui.QPushButton("modify with handles")

        self.airfoil_sep = coin.SoSeparator()
        self.spline_sep = coin.SoSeparator()
        self.upper_spline = coin.SoSeparator()
        self.lower_spline = coin.SoSeparator()
        self.ctrl_upper = None
        self.ctrl_lower = None
        self.upper_cpc = None
        self.lower_cpc = None
        self.previous_foil = None
        self.is_edit = False
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        # airfoil widget
        self.form.insert(0, self.Qairfoil_widget)
        self.Qairfoil_widget.setWindowTitle("airfoil")
        self.Qairfoil_layout.addWidget(self.Qairfoil_name)
        self.Qairfoil_layout.addWidget(self.Qimport_button)
        self.Qairfoil_layout.addWidget(self.Qfit_button)

        # selection widget
        self.layout.addWidget(self.QList_View)
        for profile in self.glider_2d.profiles:
            self.QList_View.addItem(QAirfoil_item(profile))
        self.QList_View.setMaximumHeight(100)
        self.QList_View.setCurrentRow(0)
        self.layout.addWidget(self.Qnew_button)
        self.layout.addWidget(self.Qdelete_button)
        self.QList_View.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

        # connections
        self.Qimport_button.clicked.connect(self.import_file_dialog)
        self.Qnew_button.clicked.connect(self.create_airfoil)
        self.Qdelete_button.clicked.connect(self.delete_airfoil)
        self.QList_View.currentRowChanged.connect(self.update_selection)
        self.Qairfoil_name.textChanged.connect(self.update_name)
        self.Qfit_button.clicked.connect(self.spline_edit)

    def setup_pivy(self):
        self.task_separator.addChild(self.airfoil_sep)
        self.task_separator.addChild(self.spline_sep)
        self.update_selection()
        Gui.SendMsgToActiveView("ViewFit")

    def import_file_dialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(
            parent=None,
            caption="import airfoil",
            directory='~',
            filter='*.dat',
            selectedFilter='*.dat')
        if filename[0] != "":
            self.QList_View.addItem(
                QAirfoil_item(
                    BezierProfile2D.import_from_dat(filename[0])))

    def create_airfoil(self):
        j = 0
        for index in xrange(self.QList_View.count()):
            name = self.QList_View.item(index).text()
            if "airfoil" in name:
                j += 1
        airfoil = BezierProfile2D.compute_naca(4412)
        airfoil.name = "airfoil" + str(j)
        new_item = QAirfoil_item(airfoil)
        self.QList_View.addItem(new_item)
        self.QList_View.setCurrentItem(new_item)

    @property
    def current_airfoil(self):
        if self.QList_View.currentItem() is not None:
            return self.QList_View.currentItem().airfoil
        return None

    def delete_airfoil(self):
        a = self.QList_View.currentRow()
        self.QList_View.takeItem(a)

    def update_selection(self, *args):
        if self.is_edit and self.previous_foil:
            self.previous_foil.apply_splines()
            self.unset_edit_mode()
        if self.QList_View.currentItem():
            self.Qairfoil_name.setText(self.QList_View.currentItem().text())
            self.previous_foil = self.current_airfoil
            self.update_airfoil()

    def update_name(self, *args):
        name = self.Qairfoil_name.text()
        self.QList_View.currentItem().airfoil.name = name
        self.QList_View.currentItem().setText(name)

    def update_airfoil(self, *args):
        self.airfoil_sep.removeAllChildren()
        self.airfoil_sep.addChild(
            Line(vector3D(
                self.current_airfoil), width=2).object)

    def spline_edit(self):
        if self.is_edit:
            self.current_airfoil.apply_splines()
            self.unset_edit_mode()
            self.update_airfoil()
        else:
            self.set_edit_mode()

    def set_edit_mode(self):
        if self.current_airfoil is not None:
            self.is_edit = True
            self.airfoil_sep.removeAllChildren()
            self.spline_sep.removeAllChildren()
            self.upper_cpc = ControlPointContainer(view=self.view)
            self.lower_cpc = ControlPointContainer(view=self.view)
            self.upper_cpc.control_pos = self.current_airfoil.upper_spline.controlpoints
            self.lower_cpc.control_pos = self.current_airfoil.lower_spline.controlpoints
            self.upper_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[0].fix = True
            self.upper_cpc.control_points[0].fix = True
            self.lower_cpc.control_points[-1].pos = [1., 0., 0.]
            self.upper_cpc.control_points[0].pos = [1., 0., 0.]
            self.spline_sep.addChild(self.upper_cpc)
            self.spline_sep.addChild(self.lower_cpc)
            self.spline_sep.addChild(self.lower_spline)
            self.spline_sep.addChild(self.upper_spline)
            self.upper_cpc.on_drag.append(self.upper_on_change)
            self.lower_cpc.on_drag.append(self.lower_on_change)
            self.upper_cpc.drag_release.append(self.upper_drag_release)
            self.lower_cpc.drag_release.append(self.lower_drag_release)
            self.upper_drag_release()
            self.lower_drag_release()

    def upper_on_change(self):
        self._update_upper_spline(15)

    def lower_on_change(self):
        self._update_lower_spline(15)

    def upper_drag_release(self):
        self._update_upper_spline(60)

    def lower_drag_release(self):
        self._update_lower_spline(60)

    @property
    def control_line(self):
        points = list(self.current_airfoil.upper_spline.controlpoints) +\
                 list(self.current_airfoil.lower_spline.controlpoints)[1:]
        return [[p[0], p[1], -0.01] for p in points]

    def _draw_spline(self, num):
        self.upper_spline.addChild(
            Line(self.control_line, color="grey").object)
        self.upper_spline.addChild(
            Line(vector3D(
                self.current_airfoil.upper_spline.get_sequence(num)),
                width=2).object)
        self.lower_spline.addChild(
            Line(vector3D(
                self.current_airfoil.lower_spline.get_sequence(num)),
                width=2).object)

    def _update_upper_spline(self, num=20):
        self.upper_spline.removeAllChildren()
        self.lower_spline.removeAllChildren()
        self.current_airfoil.upper_spline.controlpoints = [
            i[:-1] for i in self.upper_cpc.control_pos]
        direction = normalize(
            self.current_airfoil.upper_spline.controlpoints[-2])
        radius = norm(self.current_airfoil.lower_spline.controlpoints[1])
        new_point = - numpy.array(direction) * radius
        self.current_airfoil.lower_spline.controlpoints[1] = new_point
        self.lower_cpc.control_points[1].pos = vector3D(new_point)
        self._draw_spline(num)

    def _update_lower_spline(self, num=20):
        self.lower_spline.removeAllChildren()
        self.upper_spline.removeAllChildren()
        self.current_airfoil.lower_spline.controlpoints = [
            i[:-1] for i in self.lower_cpc.control_pos]
        direction = normalize(
            self.current_airfoil.lower_spline.controlpoints[1])
        radius = norm(self.current_airfoil.upper_spline.controlpoints[-2])
        new_point = -numpy.array(direction) * radius
        self.current_airfoil.upper_spline.controlpoints[-2] = new_point
        self.upper_cpc.control_points[-2].pos = vector3D(new_point)
        self._draw_spline(num)

    def unset_edit_mode(self):
        if self.is_edit:
            self.upper_cpc.on_drag = []
            self.lower_cpc.on_drag = []
            self.upper_cpc.drag_release = []
            self.lower_cpc.drag_release = []
            self.spline_sep.removeAllChildren()
            self.upper_cpc.remove_callbacks()
            self.lower_cpc.remove_callbacks()
            self.is_edit = False

    def accept(self):
        self.unset_edit_mode()
        profiles = []
        for index in xrange(self.QList_View.count()):
            airfoil = self.QList_View.item(index).airfoil
            airfoil.apply_splines()
            profiles.append(airfoil)
        self.glider_2d.profiles = profiles
        self.update_view_glider()
        super(airfoil_tool, self).accept()


class QAirfoil_item(QtGui.QListWidgetItem):
    def __init__(self, airfoil):
        self.airfoil = airfoil
        super(QAirfoil_item, self).__init__()
        self.setText(self.airfoil.name)
