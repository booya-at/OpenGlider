import os
from copy import deepcopy

import numpy as np
from pivy import coin

import FreeCADGui as Gui
from openglider import jsonify
from openglider.airfoil import BezierProfile2D
from openglider.vector import norm, normalize
from PySide import QtCore, QtGui

from .tools import BaseTool, ControlPointContainer, Line_old, vector3D


class AirfoilTool(BaseTool):
    widget_name = 'Selection'

    def __init__(self, obj):
        super(AirfoilTool, self).__init__(obj)
        # base_widget
        self.QList_View = QtGui.QListWidget(self.base_widget)
        self.Qdelete_button = QtGui.QPushButton('delete', self.base_widget)
        self.Qnew_button = QtGui.QPushButton('new', self.base_widget)
        self.Qcopy_button = QtGui.QPushButton('copy', self.base_widget)

        self.Qairfoil_widget = QtGui.QWidget()
        self.Qairfoil_layout = QtGui.QFormLayout(self.Qairfoil_widget)
        self.Qimport_button = QtGui.QPushButton('import airfoil')
        self.Qexport_button = QtGui.QPushButton('export airfoil')
        self.Qfit_button = QtGui.QPushButton('modify with handles')
        self.Qnum_points_upper = QtGui.QSpinBox(self.base_widget)
        self.Qnum_points_lower = QtGui.QSpinBox(self.base_widget)
        self.Qshow_pressure_dist = QtGui.QCheckBox("show pressure", parent=self.base_widget)
        self.Qshow_curvature_dist = QtGui.QCheckBox("show curvature", parent=self.base_widget)
        self.Qshow_theoretic_stress_dist = QtGui.QCheckBox("theoretic_stress", parent=self.base_widget)
        self.Qalpha = QtGui.QDoubleSpinBox(parent=self.base_widget)

        self.airfoil_sep = coin.SoSeparator()
        self.spline_sep = coin.SoSeparator()
        self.upper_spline = coin.SoSeparator()
        self.lower_spline = coin.SoSeparator()
        self.pressure_sep = coin.SoSeparator()
        self.curvature_sep = coin.SoSeparator()
        self.theoretic_stress_sep = coin.SoSeparator()
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
        self.Qairfoil_layout.addWidget(self.Qimport_button)
        self.Qairfoil_layout.addWidget(self.Qexport_button)
        self.Qairfoil_layout.addWidget(self.Qfit_button)
        self.Qairfoil_layout.addWidget(self.Qnum_points_upper)
        self.Qairfoil_layout.addWidget(self.Qnum_points_lower)
        self.Qairfoil_layout.addWidget(self.Qshow_pressure_dist)
        self.Qairfoil_layout.addWidget(self.Qshow_curvature_dist)
        self.Qairfoil_layout.addWidget(self.Qshow_theoretic_stress_dist)
        self.Qairfoil_layout.addWidget(self.Qalpha)


        self.Qnum_points_upper.setMaximum(9)
        self.Qnum_points_upper.setMinimum(4)
        self.Qnum_points_upper.setDisabled(True)
        self.Qnum_points_upper.valueChanged.connect(self.fit_upper_spline)

        self.Qnum_points_lower.setMaximum(9)
        self.Qnum_points_lower.setMinimum(4)
        self.Qnum_points_lower.setDisabled(True)
        self.Qnum_points_lower.valueChanged.connect(self.fit_lower_spline)

        self.Qshow_pressure_dist.setDisabled(True)
        self.Qshow_curvature_dist.setDisabled(True)
        self.Qshow_theoretic_stress_dist.setDisabled(True)
        self.Qalpha.setDisabled(True)
        self.Qalpha.setValue(9.0)

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

        # connections
        self.QList_View.itemChanged.connect(self.update_airfoil)
        self.Qimport_button.clicked.connect(self.import_file_dialog)
        self.Qexport_button.clicked.connect(self.export_file_dialog)
        self.Qnew_button.clicked.connect(self.create_airfoil)
        self.Qdelete_button.clicked.connect(self.delete_airfoil)
        self.QList_View.currentRowChanged.connect(self.update_selection)
        self.Qfit_button.clicked.connect(self.spline_edit)
        self.Qcopy_button.clicked.connect(self.copy_airfoil)
        self.Qshow_pressure_dist.stateChanged.connect(self.pressure_vis)
        self.Qshow_curvature_dist.stateChanged.connect(self.curvature_vis)
        self.Qshow_theoretic_stress_dist.stateChanged.connect(self.theoretic_stress_vis)
        self.Qalpha.valueChanged.connect(self.pressure_vis)
        self.Qalpha.valueChanged.connect(self.theoretic_stress_vis)

    def setup_pivy(self):
        self.task_separator += [self.airfoil_sep, self.spline_sep, 
                                self.pressure_sep, self.curvature_sep,
                                self.theoretic_stress_sep]
        self.update_selection()
        Gui.SendMsgToActiveView('ViewFit')

    def import_file_dialog(self):
        filename = QtGui.QFileDialog.getOpenFileName(
            parent=None,
            caption='import airfoil',
            directory='~',
            filter='*.dat *.json',
            selectedFilter='*.dat *.json')
        if filename[0] != '':
            name, format = os.path.splitext(filename[0])
            if format == ".dat":
                self.QList_View.addItem(
                    QAirfoil_item(
                        BezierProfile2D.import_from_dat(filename[0])))
            elif format == ".json":
                with open(filename[0], "r") as fp:
                    airfoil = jsonify.load(fp)["data"]
                    self.QList_View.addItem(
                        QAirfoil_item(airfoil))

    def export_file_dialog(self):
        filename = QtGui.QFileDialog.getSaveFileName(
            parent=None,
            caption='import airfoil',
            directory='~',
            filter='*.dat *.json',
            selectedFilter='*.dat *.json')
        if filename[0] != '':
            name, format = os.path.splitext(filename[0])
            if format == ".dat":
                self.current_airfoil.export_dat(filename[0])
            elif format == ".json":
                with open(filename[0], "w") as fp:
                    jsonify.dump(self.current_airfoil, fp)

    def copy_airfoil(self):
        self.QList_View.addItem(
            QAirfoil_item(
                deepcopy(self.current_airfoil)))

    def change_text(self):
        print("change_text")
        if self.QList_View.currentItem():
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
            self.previous_foil = self.current_airfoil
            self.update_airfoil()

    def update_name(self, name):
        self.QList_View.currentItem().airfoil.name = name
        self.QList_View.currentItem().setText(name)

    def update_airfoil(self, thin=False, *args):
        self.airfoil_sep.removeAllChildren()
        for index in range(self.QList_View.count()):
            airfoil_item = self.QList_View.item(index)
            if airfoil_item.checkState() or index == self.QList_View.currentRow():
                airfoil = airfoil_item.airfoil
                width = 0.5
                if index == self.QList_View.currentRow() and not thin:
                    width = 2
                self.airfoil_sep += [Line_old(vector3D(airfoil), width=width).object]

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
            self.QList_View.setEnabled(False)
            airfoil = self.current_airfoil
            self.Qnum_points_upper.setValue(len(airfoil.upper_spline.controlpoints))
            self.Qnum_points_lower.setValue(len(airfoil.lower_spline.controlpoints))
            self.is_edit = True
            self.Qnum_points_upper.setDisabled(False)
            self.Qnum_points_lower.setDisabled(False)
            try:
                import parabem
                from parabem.pan2d import DirichletDoublet0Source0Case2
            except ImportError:
                print("pressure visualization needs parabem")
            else:
                self.Qshow_pressure_dist.setDisabled(False)
                self.Qshow_curvature_dist.setDisabled(False)
                self.Qshow_theoretic_stress_dist.setDisabled(False)
            self.update_airfoil(thin=True)
            self.spline_sep.removeAllChildren()
            self.airfoil_sep += [Line_old(self.current_airfoil.data).object]
            self.upper_cpc = ControlPointContainer(self.rm)
            self.lower_cpc = ControlPointContainer(self.rm)
            self.upper_cpc.control_pos = airfoil.upper_spline.controlpoints
            self.lower_cpc.control_pos = airfoil.lower_spline.controlpoints
            self.constrain_upper_points()
            self.constrain_lower_points()

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
        if self.Qshow_pressure_dist.isChecked():
            self.pressure_vis()
        if self.Qshow_curvature_dist.isChecked():
            self.curvature_vis()
        if self.Qshow_theoretic_stress_dist.isChecked():
            self.theoretic_stress_vis()

    def lower_on_change(self):
        self._update_lower_spline(100)
        if self.Qshow_pressure_dist.isChecked():
            self.pressure_vis()
        if self.Qshow_curvature_dist.isChecked():
            self.curvature_vis()
        if self.Qshow_theoretic_stress_dist.isChecked():
            self.theoretic_stress_vis()

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
            Line_old(self.upper_control_line, color='grey').object]
        self.upper_spline += [
            Line_old(vector3D(
                self.current_airfoil.upper_spline.get_sequence(num)),
                width=2).object]

    def draw_lower_spline(self, num):
        self.lower_spline += [
            Line_old(self.lower_control_line, color='grey').object]
        self.lower_spline += [
            Line_old(vector3D(
                self.current_airfoil.lower_spline.get_sequence(num)),
                width=2).object]

    def _update_upper_spline(self, num=50):
        self.upper_spline.removeAllChildren()
        # self.upper_cpc.control_points[-2].set_x(0.)
        self.current_airfoil.upper_spline.controlpoints = [
            i[:-1] for i in self.upper_cpc.control_pos]
        self.draw_upper_spline(num)

    def _update_lower_spline(self, num=50):
        self.lower_spline.removeAllChildren()
        # self.lower_cpc.control_points[1].set_x(0.)
        self.current_airfoil.lower_spline.controlpoints = [
            i[:-1] for i in self.lower_cpc.control_pos]
        self.draw_lower_spline(num)

    def unset_edit_mode(self):
        if self.is_edit:
            self.QList_View.setEnabled(True)
            self.Qnum_points_upper.setDisabled(True)
            self.Qnum_points_lower.setDisabled(True)
            self.Qshow_pressure_dist.setDisabled(True)
            self.Qshow_pressure_dist.setChecked(False)
            self.upper_cpc.on_drag = []
            self.lower_cpc.on_drag = []
            self.upper_cpc.drag_release = []
            self.lower_cpc.drag_release = []
            self.spline_sep.removeAllChildren()
            self.upper_cpc.remove_callbacks()
            self.lower_cpc.remove_callbacks()
            self.is_edit = False

    def constrain_upper_points(self):
        self.upper_cpc.control_points[-1].pos = [0., 0., 0.]
        self.upper_cpc.control_points[0].pos = [1., 0., 0.]
        self.upper_cpc.control_points[-1].enabled = False
        self.upper_cpc.control_points[0].enabled = False
        t_marker = self.upper_cpc.control_points[-2]
        p = t_marker.points
        p[0][0] = 0.
        t_marker.points = p
        t_marker.constrained = [0., 1., 0.]

    def constrain_lower_points(self):
        self.lower_cpc.control_points[0].pos = [0., 0., 0.]
        self.lower_cpc.control_points[-1].pos = [1., 0., 0.]
        self.lower_cpc.control_points[-1].enabled = False
        self.lower_cpc.control_points[0].enabled = False
        t_marker = self.lower_cpc.control_points[1]
        p = t_marker.points
        p[0][0] = 0.
        t_marker.points = p
        t_marker.constrained = [0., 1., 0.]

    def fit_upper_spline(self, num):
        if self.is_edit:
            self.current_airfoil.apply_splines()
            self.current_airfoil.upper_spline = self.current_airfoil.fit_upper(control_num=num)
            self.upper_cpc.control_pos = vector3D(self.current_airfoil.upper_spline.controlpoints)
            self.constrain_upper_points()
            self._update_upper_spline()

    def fit_lower_spline(self, num):
        if self.is_edit:
            self.current_airfoil.apply_splines()
            self.current_airfoil.lower_spline = self.current_airfoil.fit_lower(control_num=num)
            self.lower_cpc.control_pos = vector3D(self.current_airfoil.lower_spline.controlpoints)
            self.constrain_lower_points()
            self._update_lower_spline()

    def accept(self):
        self.unset_edit_mode()
        profiles = []
        for index in range(self.QList_View.count()):
            airfoil = self.QList_View.item(index).airfoil
            airfoil.name = self.QList_View.item(index).text()
            airfoil.apply_splines()
            profiles.append(airfoil)
        super(AirfoilTool, self).accept()
        self.parametric_glider.profiles = profiles
        self.update_view_glider()

    def reject(self):
        self.unset_edit_mode()
        super(AirfoilTool, self).reject()

    def pressure_vis(self):
        self.pressure_sep.removeAllChildren()
        if self.Qshow_pressure_dist.isChecked():
            self.Qalpha.setEnabled(True)
            self.show_pressure()
        else:
            print("is unchecked")
            self.Qalpha.setEnabled(False)

    def curvature_vis(self):
        self.curvature_sep.removeAllChildren()
        if self.Qshow_curvature_dist.isChecked():
            self.show_curvature()

    def theoretic_stress_vis(self):
        self.theoretic_stress_sep.removeAllChildren()
        if self.Qshow_theoretic_stress_dist.isChecked():
            self.show_theoretic_stress()
        
    def show_pressure(self):
        import parabem
        from parabem.pan2d import DirichletDoublet0Source0Case2

        # 1. get the panels from the airfoil
        self.current_airfoil.apply_splines()
        coords = self.current_airfoil.data[:-1]
        pans = []
        vertices = []
        vertices = [parabem.PanelVector2(*i) for i in coords]
        vertices[0].wake_vertex = True
        for i, coord in enumerate(coords):
            j = (i+1 if (i + 1) < len(coords) else 0)
            pan = parabem.Panel2([vertices[i], vertices[j]])
            pans.append(pan)
        # 2. compute pressure
        case = DirichletDoublet0Source0Case2(pans)
        alpha = np.deg2rad(self.Qalpha.value())
        case.v_inf = parabem.Vector2(np.cos(alpha), np.sin(alpha))
        case.run()
        for pan in pans:
            p0 = pan.center
            p1 = p0 + pan.n * pan.cp * 0.03
            l = [[*p0, 0.], [*p1, 0.]]  # adding z-value
            self.pressure_sep += Line_old(l).object
        return True

    def show_curvature(self):
        self.current_airfoil.apply_splines()
        data = self.current_airfoil.data[1:-1]
        radius = self.current_airfoil.curvature_radius
        normals = np.array(self.current_airfoil.normvectors)[1:-1]
        for r, p, n in zip(radius, data, normals):
            p1 = p + n * 1. / r * 0.1
            l = [[*p, 0.], [*p1, 0.]]
            self.curvature_sep += Line_old(l).object

    def show_theoretic_stress(self):
        import parabem
        from parabem.pan2d import DirichletDoublet0Source0Case2

        # 1. get the panels from the airfoil
        self.current_airfoil.apply_splines()
        coords = self.current_airfoil.data[:-1]
        pans = []
        vertices = []
        vertices = [parabem.PanelVector2(*i) for i in coords]
        vertices[0].wake_vertex = True
        for i, coord in enumerate(coords):
            j = (i+1 if (i + 1) < len(coords) else 0)
            pan = parabem.Panel2([vertices[i], vertices[j]])
            pans.append(pan)
        # 2. compute pressure
        case = DirichletDoublet0Source0Case2(pans)
        alpha = np.deg2rad(self.Qalpha.value())
        case.v_inf = parabem.Vector2(np.cos(alpha), np.sin(alpha))
        case.run()
        radius = self.current_airfoil.curvature_radius
        data = self.current_airfoil.data[1:-1]
        radius = self.current_airfoil.curvature_radius
        normals = np.array(self.current_airfoil.normvectors)[1:-1]
        cp = np.array([pan.cp for pan in pans])
        cp = (cp[:-1] + cp[1:]) / 2
        for r, p, n, c in zip(radius, data, normals, cp):
            p1 = p - n * (c - 1) * r * 0.02
            l = [[*p, 0.], [*p1, 0.]]
            self.theoretic_stress_sep += Line_old(l).object




class QAirfoil_item(QtGui.QListWidgetItem):
    def __init__(self, airfoil):
        self.airfoil = airfoil
        super(QAirfoil_item, self).__init__()
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.setFlags(self.flags() | QtCore.Qt.ItemIsUserCheckable)
        self.setText(self.airfoil.name)
        self.setCheckState(QtCore.Qt.Unchecked)

    def rename(self):
        print("renaming")
        self.airfoil.name = self.text()
