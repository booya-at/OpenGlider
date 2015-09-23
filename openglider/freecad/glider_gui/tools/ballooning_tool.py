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

        # connections
        self.Qnew_button.clicked.connect(self.create_ballooning)
        self.Qdelete_button.clicked.connect(self.delete_ballooning)
        self.QList_View.currentRowChanged.connect(self.update_selection)
        self.Qballooning_name.textChanged.connect(self.update_name)
        self.Qfit_button.clicked.connect(self.spline_edit)

    def setup_pivy(self):
        self.task_separator.addChild(self.ballooning_sep)
        self.task_separator.addChild(self.spline_sep)
        self.update_selection()
        self.grid = coin.SoSeparator()
        self.task_separator.addChild(self.grid)
        self._update_grid()
        Gui.SendMsgToActiveView("ViewFit")

    def _update_grid(self, grid_x=None, grid_y=None):
        grid_x = grid_x or numpy.linspace(0., 1., int(10 + 1))
        grid_y = grid_y or numpy.linspace(-0.1, 0.1, int(10 + 1))
        self.grid.removeAllChildren()
        x_points_lower = [[x, grid_y[0], -0.001] for x in grid_x]
        x_points_upper = [[x, grid_y[-1], -0.001] for x in grid_x]
        y_points_lower = [[grid_x[0], y, -0.001] for y in grid_y]
        y_points_upper = [[grid_x[-1], y, -0.001] for y in grid_y]
        for l in zip(x_points_lower, x_points_upper):
            self.grid.addChild(Line(l, color="grey").object)
        for l in zip(y_points_lower, y_points_upper):
            self.grid.addChild(Line(l, color="grey").object)
        for l in y_points_upper[::10]:
            textsep = coin.SoSeparator()
            text = coin.SoText2()
            trans = coin.SoTranslation()
            trans.translation = l
            text.string = str(l[1])
            textsep.addChild(trans)
            self.grid.addChild(textsep)
            textsep.addChild(text)

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
        self.draw_lower_spline(70)
        self.draw_upper_spline(70)
        self.ballooning_sep.addChild(self.upper_spline)
        self.ballooning_sep.addChild(self.lower_spline)

    def spline_edit(self):
        if self.is_edit:
            # self.current_ballooning.ballooning.apply_splines()
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
        self._update_upper_spline(30)

    def lower_on_change(self):
        self._update_lower_spline(30)

    def upper_drag_release(self):
        self._update_upper_spline(70)

    def lower_drag_release(self):
        self._update_lower_spline(70)

    def _update_upper_spline(self, num):
        self.current_ballooning.upper_controlpoints = [
            i[:-1] for i in self.upper_cpc.control_pos]
        self.draw_upper_spline(num)

    def draw_upper_spline(self, num):
        self.upper_spline.removeAllChildren()
        l = Line(vector3D(self.current_ballooning.get_expl_upper_spline(num)),
                 color="red", width=2)
        self.upper_spline.addChild(l.object)

    def _update_lower_spline(self, num):
        self.current_ballooning.lower_controlpoints = [
            i[:-1] for i in self.lower_cpc.control_pos]
        self.draw_lower_spline(num)

    def draw_lower_spline(self, num):
        self.lower_spline.removeAllChildren()
        l = Line(vector3D(self.current_ballooning.get_expl_lower_spline(num)),
                 color="red", width=2)
        self.lower_spline.addChild(l.object)

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
        balloonings = []
        for index in xrange(self.QList_View.count()):
            ballooning = self.QList_View.item(index)
            ballooning.apply_splines()
            balloonings.append(ballooning.ballooning)
        self.glider_2d.balloonings = balloonings
        self.update_view_glider()
        super(ballooning_tool, self).accept()


class QBalooning(QtGui.QListWidgetItem):
    def __init__(self, ballooning):
        self.ballooning = ballooning
        super(QBalooning, self).__init__()
        self.setText(self.ballooning.name)
        self.upper_controlpoints = self.ballooning.upper_spline.controlpoints
        self.lower_controlpoints = numpy.array(
            [1, -1]) * self.ballooning.lower_spline.controlpoints

    def get_expl_lower_spline(self, num):
        self.ballooning.lower_spline.controlpoints = numpy.array(
            [1, -1]) * self.lower_controlpoints
        seq = self.ballooning.lower_spline.get_sequence(num)
        return seq * numpy.array([1, -1])

    def get_expl_upper_spline(self, num):
        self.ballooning.upper_spline.controlpoints = self.upper_controlpoints
        seq = self.ballooning.upper_spline.get_sequence(num)
        return seq

    def apply_splines(self):
        self.ballooning.controlpoints = [
            self.upper_controlpoints,
            numpy.array([1, -1]) * self.lower_controlpoints]
