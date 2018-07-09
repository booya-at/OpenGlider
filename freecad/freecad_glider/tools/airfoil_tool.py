import numpy
from pivy import coin
from PySide import QtGui, QtCore
from copy import deepcopy

import FreeCADGui as Gui

from openglider.airfoil import BezierProfile2D
from openglider.vector import normalize, norm
from ._tools import BaseTool
from . import pivy_primitives as pp

def refresh():
    pass

class AirfoilTool(BaseTool):
    widget_name = 'Selection'

    def __init__(self, obj):
        super(AirfoilTool, self).__init__(obj)
        # base_widget
        self.QList_View = QtGui.QListWidget(self.base_widget)
        self.Qdelete_button = QtGui.QPushButton('delete', self.base_widget)
        self.Qnew_button = QtGui.QPushButton('new', self.base_widget)
        self.Qcopy_button = QtGui.QPushButton('copy', self.base_widget)
        self.Qairfoil_name = QtGui.QLineEdit()

        self.Qairfoil_widget = QtGui.QWidget()
        self.Qairfoil_layout = QtGui.QFormLayout(self.Qairfoil_widget)
        self.Qimport_button = QtGui.QPushButton('import airfoil')
        self.Qexport_button = QtGui.QPushButton('export airfoil')
        self.Qfit_button = QtGui.QPushButton('modify with handles')
        self.Qnum_points_upper = QtGui.QSpinBox(self.base_widget)
        self.Qnum_points_lower = QtGui.QSpinBox(self.base_widget)

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

        # setup the GUI
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        # airfoil widget
        self.form.insert(0, self.Qairfoil_widget)
        self.Qairfoil_widget.setWindowTitle('airfoil')
        self.Qairfoil_layout.addWidget(self.Qairfoil_name)
        self.Qairfoil_layout.addWidget(self.Qimport_button)
        self.Qairfoil_layout.addWidget(self.Qexport_button)
        self.Qairfoil_layout.addWidget(self.Qfit_button)
        self.Qairfoil_layout.addWidget(self.Qnum_points_upper)
        self.Qairfoil_layout.addWidget(self.Qnum_points_lower)


        self.Qnum_points_upper.setMaximum(10)
        self.Qnum_points_upper.setMinimum(4)
        self.Qnum_points_upper.setDisabled(True)
        self.Qnum_points_upper.valueChanged.connect(self.fit_upper_spline)

        self.Qnum_points_lower.setMaximum(10)
        self.Qnum_points_lower.setMinimum(4)
        self.Qnum_points_lower.setDisabled(True)
        self.Qnum_points_lower.valueChanged.connect(self.fit_lower_spline)

        # selection widget
        self.layout.addWidget(self.QList_View)
        for profile in self.parametric_glider.profiles:
            self.QList_View.addItem(QAirfoil_item(profile))
        self.QList_View.setMaximumHeight(100)
        self.QList_View.setCurrentRow(0)
        self.layout.addWidget(self.Qnew_button)
        self.layout.addWidget(self.Qdelete_button)
        self.layout.addWidget(self.Qcopy_button)
        self.QList_View.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.QList_View.currentTextChanged.connect(self.change_text)

        # connections
        self.Qimport_button.clicked.connect(self.import_file_dialog)
        self.Qexport_button.clicked.connect(self.export_file_dialog)
        self.Qnew_button.clicked.connect(self.create_airfoil)
        self.Qdelete_button.clicked.connect(self.delete_airfoil)
        self.QList_View.currentRowChanged.connect(self.update_selection)
        self.Qairfoil_name.textChanged.connect(self.update_name)
        self.Qfit_button.clicked.connect(self.spline_edit)
        self.Qcopy_button.clicked.connect(self.copy_airfoil)

    def setup_pivy(self):
        self.task_separator += [self.airfoil_sep, self.spline_sep]
        self.update_selection()
        Gui.SendMsgToActiveView('ViewFit')

    def import_file_dialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(
            parent=None,
            caption='import airfoil',
            directory='~',
            filter='*.dat',
            selectedFilter='*.dat')
        if filename[0] != '':
            self.QList_View.addItem(
                QAirfoil_item(
                    BezierProfile2D.import_from_dat(filename[0])))

    def export_file_dialog(self):
        filename = QtGui.QFileDialog.getSaveFileName(
            parent=None,
            caption='import airfoil',
            directory='~',
            filter='*.dat',
            selectedFilter='*.dat')
        if filename[0] != '':
            self.current_airfoil.export_dat(filename[0] + filename[1][1:])

    def copy_airfoil(self):
        self.QList_View.addItem(
            QAirfoil_item(
                deepcopy(self.current_airfoil)))

    def change_text(self):
        self.QList_View.currentItem().rename()

    def create_airfoil(self):
        j = 0
        for index in range(self.QList_View.count()):
            name = self.QList_View.item(index).text()
            if 'airfoil' in name:
                j += 1
        airfoil = BezierProfile2D.compute_naca(4412)
        airfoil.name = 'airfoil' + str(j)
        new_item = QAirfoil_item(airfoil)
        self.QList_View.addItem(new_item)
        self.QList_View.setCurrentItem(new_item)

    @property
    def current_airfoil(self):
        if self.QList_View.currentItem() is not None:
            return self.QList_View.currentItem().airfoil
        return None

    @current_airfoil.setter
    def current_airfoil(self, airfoil):
        self.QList_View.currentItem().airfoil = airfoil

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
        self.airfoil_sep += [pp.Line(pp.vector3D(self.current_airfoil), width=2).object]

    def spline_edit(self):
        if self.is_edit:
            self.current_airfoil.apply_splines()
            self.unset_edit_mode()
            self.update_airfoil()
        else:
            if not isinstance(self.current_airfoil, BezierProfile2D):
                self.current_airfoil = BezierProfile2D.from_profile_2d(self.current_airfoil)
                self.update_selection()
            self.set_edit_mode()

    def set_edit_mode(self):
        if self.current_airfoil is not None:
            airfoil = self.current_airfoil
            self.Qnum_points_upper.setValue(len(airfoil.upper_spline.controlpoints))
            self.Qnum_points_lower.setValue(len(airfoil.lower_spline.controlpoints))
            self.is_edit = True
            self.Qnum_points_upper.setDisabled(False)
            self.Qnum_points_lower.setDisabled(False)
            self.airfoil_sep.removeAllChildren()
            self.spline_sep.removeAllChildren()
            self.airfoil_sep += [pp.Line(self.current_airfoil.data).object]
            self.upper_cpc = pp.ControlPointContainer(view=self.view)
            self.lower_cpc = pp.ControlPointContainer(view=self.view)
            self.upper_cpc.control_pos = airfoil.upper_spline.controlpoints
            self.lower_cpc.control_pos = airfoil.lower_spline.controlpoints
            self.upper_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[0].fix = True
            self.upper_cpc.control_points[0].fix = True
            self.lower_cpc.control_points[-1].pos = [1., 0., 0.]
            self.upper_cpc.control_points[0].pos = [1., 0., 0.]
            self.spline_sep += [self.upper_cpc, self.lower_cpc]
            self.spline_sep += [self.lower_spline, self.upper_spline]
            self.upper_cpc.on_drag.append(self.upper_on_change)
            self.lower_cpc.on_drag.append(self.lower_on_change)
            self.upper_cpc.drag_release.append(self.upper_drag_release)
            self.lower_cpc.drag_release.append(self.lower_drag_release)
            self.upper_drag_release()
            self.lower_drag_release()

    def upper_on_change(self):
        self._update_upper_spline(100)

    def lower_on_change(self):
        self._update_lower_spline(100)

    def upper_drag_release(self):
        self._update_upper_spline(200)

    def lower_drag_release(self):
        self._update_lower_spline(200)

    @property
    def upper_control_line(self):
        points = self.current_airfoil.upper_spline.controlpoints
        return [[p[0], p[1], -0.01] for p in points]

    @property
    def lower_control_line(self):
        points = self.current_airfoil.lower_spline.controlpoints
        return [[p[0], p[1], -0.01] for p in points]

    def draw_upper_spline(self, num):
        self.upper_spline += [
            pp.Line(self.upper_control_line, color='grey').object]
        self.upper_spline += [
            pp.Line(pp.vector3D(
                self.current_airfoil.upper_spline.get_sequence(num)),
                width=2).object]

    def draw_lower_spline(self, num):
        self.lower_spline += [
            pp.Line(self.lower_control_line, color='grey').object]
        self.lower_spline += [
            pp.Line(pp.vector3D(
                self.current_airfoil.lower_spline.get_sequence(num)),
                width=2).object]

    def _update_upper_spline(self, num=50):
        self.upper_spline.removeAllChildren()
        self.upper_cpc.control_points[-2].set_x(0.)
        self.current_airfoil.upper_spline.controlpoints = [
            i[:-1] for i in self.upper_cpc.control_pos]
        self.draw_upper_spline(num)

    def _update_lower_spline(self, num=50):
        self.lower_spline.removeAllChildren()
        self.lower_cpc.control_points[1].set_x(0.)
        self.current_airfoil.lower_spline.controlpoints = [
            i[:-1] for i in self.lower_cpc.control_pos]
        self.draw_lower_spline(num)

    def unset_edit_mode(self):
        if self.is_edit:
            self.Qnum_points_upper.setDisabled(True)
            self.Qnum_points_lower.setDisabled(True)
            self.upper_cpc.on_drag = []
            self.lower_cpc.on_drag = []
            self.upper_cpc.drag_release = []
            self.lower_cpc.drag_release = []
            self.spline_sep.removeAllChildren()
            self.upper_cpc.remove_callbacks()
            self.lower_cpc.remove_callbacks()
            self.is_edit = False

    def fit_upper_spline(self, num):
        if self.is_edit:
            self.current_airfoil.apply_splines()
            self.current_airfoil.upper_spline = self.current_airfoil.fit_upper(control_num=num)
            self.upper_cpc.control_pos = pp.vector3D(self.current_airfoil.upper_spline.controlpoints)
            self.upper_cpc.control_points[-1].fix = True
            self.upper_cpc.control_points[0].fix = True
            self._update_upper_spline()

    def fit_lower_spline(self, num):
        if self.is_edit:
            self.current_airfoil.apply_splines()
            self.current_airfoil.lower_spline = self.current_airfoil.fit_lower(control_num=num)
            self.lower_cpc.control_pos = pp.vector3D(self.current_airfoil.lower_spline.controlpoints)
            self.lower_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[0].fix = True
            self._update_lower_spline()

    def accept(self):
        self.unset_edit_mode()
        profiles = []
        for index in range(self.QList_View.count()):
            airfoil = self.QList_View.item(index).airfoil
            airfoil.apply_splines()
            profiles.append(airfoil)
        super(AirfoilTool, self).accept()
        self.parametric_glider.profiles = profiles
        self.update_view_glider()

    def reject(self):
        self.unset_edit_mode()
        super(AirfoilTool, self).reject()


class QAirfoil_item(QtGui.QListWidgetItem):
    def __init__(self, airfoil):
        self.airfoil = airfoil
        super(QAirfoil_item, self).__init__()
        self.setText(self.airfoil.name)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

    def rename(self):
        self.airfoil.name = self.text()
