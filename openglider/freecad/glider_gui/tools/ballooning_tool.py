from __future__ import division

import numpy
import FreeCADGui as Gui
from _tools import base_tool, QtGui
from pivy_primitives import Line, vector3D, ControlPointContainer, coin
from openglider.glider.ballooning import BallooningBezier


class ballooning_tool(base_tool):
    def __init__(self, obj):
        super(ballooning_tool, self).__init__(obj, widget_name="selection")
        # base_widget
        self.QList_View = QtGui.QListWidget(self.base_widget)
        self.Qdelete_button = QtGui.QPushButton("delete", self.base_widget)
        self.Qnew_button = QtGui.QPushButton("new", self.base_widget)
        self.Qballooning_name = QtGui.QLineEdit()

        self.Qballooning_widget = QtGui.QWidget()
        self.Qballooning_layout = QtGui.QFormLayout(self.Qballooning_widget)
        self.Qfit_button = QtGui.QPushButton("modify with handles")

        self.ballooning_sep = coin.SoSeparator()
        self.spline_sep = coin.SoSeparator()
        self.upper_spline = coin.SoSeparator()
        self.lower_spline = coin.SoSeparator()
        self.ctrl_upper = None
        self.ctrl_lower = None
        self.upper_cpc = ControlPointContainer([], self.view)
        self.lower_cpc = ControlPointContainer([], self.view)
        self.previous_foil = None
        self.is_edit = False
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        # ballooning widget
        self.form.insert(0, self.Qballooning_widget)
        self.Qballooning_widget.setWindowTitle("ballooning")
        self.Qballooning_layout.addWidget(self.Qballooning_name)
        self.Qballooning_layout.addWidget(self.Qfit_button)

        # selection widget
        self.layout.addWidget(self.QList_View)
        for ballooning in self.glider_2d.balloonings:
            self.QList_View.addItem(QBalooning(ballooning))
        self.QList_View.setMaximumHeight(100)
        self.QList_View.setCurrentRow(0)
        self.layout.addWidget(self.Qnew_button)
        self.layout.addWidget(self.Qdelete_button)
        self.QList_View.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

        #connections
        self.Qnew_button.clicked.connect(self.create_ballooning)
        self.Qdelete_button.clicked.connect(self.delete_ballooning)
        # self.QList_View.currentRowChanged.connect(self.update_selection)
        # self.Qballooning_name.textChanged.connect(self.update_name)
        self.Qfit_button.clicked.connect(self.spline_edit)

    def setup_pivy(self):
        self.task_separator.addChild(self.ballooning_sep)
        self.task_separator.addChild(self.spline_sep)
        self.update_selection()
        Gui.SendMsgToActiveView("ViewFit")

    def create_ballooning(self):
        j = 0
        for index in xrange(self.QList_View.count()):
            name = self.QList_View.item(index).text()
            if "ballooning" in name:
                j += 1
        ballooning = BallooningBezier()
        ballooning.name = "ballooning" + str(j)
        new_item = QBalooning(ballooning)
        self.QList_View.addItem(new_item)
        self.QList_View.setCurrentItem(new_item)

    @property
    def current_ballooning(self):
        if self.QList_View.currentItem() is not None:
            return self.QList_View.currentItem()
        return None

    def delete_ballooning(self):
        a = self.QList_View.currentRow()
        self.QList_View.takeItem(a)

    def update_selection(self, *args):
        # if self.is_edit and self.previous_foil:
        #     self.previous_foil.apply_splines()
        #     self.unset_edit_mode()
        if self.QList_View.currentItem():
            self.Qballooning_name.setText(self.QList_View.currentItem().text())
            self.previous_foil = self.current_ballooning
            self.update_ballooning()

    def update_name(self, *args):
        name = self.Qballooning_name.text()
        self.current_ballooning.ballooning.name = name
        self.current_ballooning.setText(name)

    def update_ballooning(self, *args):
        self.ballooning_sep.removeAllChildren()
        self.upper_cpc.control_points = self.current_ballooning.upper_controlpoints
        self.lower_cpc.control_points = self.current_ballooning.lower_controlpoints

    def spline_edit(self):
        if self.is_edit:
            self.current_ballooning.ballooning.apply_splines()
            self.unset_edit_mode()
            self.update_ballooning()
        else:
            self.set_edit_mode()

    def set_edit_mode(self):
        if self.current_ballooning is not None:
            self.is_edit = True
            self.ballooning_sep.removeAllChildren()
            self.spline_sep.removeAllChildren()
            self.upper_cpc = ControlPointContainer(view=self.view)
            self.lower_cpc = ControlPointContainer(view=self.view)
            self.upper_cpc.control_pos = self.current_ballooning.upper_controlpoints
            self.lower_cpc.control_pos = self.current_ballooning.lower_controlpoints
            self.upper_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[0].fix = True
            self.upper_cpc.control_points[0].fix = True
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

    def _draw_spline(self, num):
        self.upper_spline.addChild(Line(vector3D(self.current_ballooning.upper_controlpoints), color="gray").object)
        self.upper_spline.addChild(Line(vector3D(self.current_ballooning.get_expl_upper_spline(num))).object)
        self.lower_spline.addChild(Line(vector3D(self.current_ballooning.lower_controlpoints), color="gray").object)
        self.lower_spline.addChild(Line(vector3D(self.current_ballooning.get_expl_lower_spline(num))).object)

    def _update_upper_spline(self, num=20):
        self.upper_spline.removeAllChildren()
        self.lower_spline.removeAllChildren()
        self.current_ballooning.upper_controlpoints =[i[:-1] for i in self.upper_cpc.control_pos]
        self._draw_spline(num)

    def _update_lower_spline(self, num=20):
        self.lower_spline.removeAllChildren()
        self.upper_spline.removeAllChildren()
        self.current_ballooning.lower_controlpoints =[i[:-1] for i in self.lower_cpc.control_pos]
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
        super(ballooning_tool, self).accept()


class QBalooning(QtGui.QListWidgetItem):
    def __init__(self, ballooning):
        self.ballooning = ballooning
        super(QBalooning, self).__init__()
        self.setText(self.ballooning.name)
        self.upper_controlpoints = self.ballooning.upper_spline.controlpoints
        self.lower_controlpoints = numpy.array([1, -1]) * self.ballooning.lower_spline.controlpoints

    def get_expl_lower_spline(self, num):
        self.ballooning.lower_spline.controlpoints = numpy.array([1, -1]) * self.lower_controlpoints
        seq = self.ballooning.lower_spline.get_sequence(num)
        return seq * numpy.array([1, -1])

    def get_expl_upper_spline(self, num):
        self.ballooning.upper_spline.controlpoints = self.upper_controlpoints
        seq = self.ballooning.upper_spline.get_sequence(num)
        return seq
