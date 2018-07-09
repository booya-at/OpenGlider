from __future__ import division

from PySide import QtGui, QtCore
import numpy
import FreeCADGui as Gui
from ._tools import BaseTool, QtGui, spline_select
from .pivy_primitives import Line, vector3D, ControlPointContainer, coin
from openglider.glider.ballooning import BallooningBezier


def refresh():
    pass


class BallooningTool(BaseTool):
    widget_name = 'Selection'
    scale_y = 5

    def __init__(self, obj):
        super(BallooningTool, self).__init__(obj)
        # base_widget
        self.QList_View = QtGui.QListWidget(self.base_widget)
        self.Qdelete_button = QtGui.QPushButton('delete', self.base_widget)
        self.Qnew_button = QtGui.QPushButton('new', self.base_widget)
        self.Qballooning_name = QtGui.QLineEdit()

        self.Qballooning_widget = QtGui.QWidget()
        self.Qballooning_layout = QtGui.QFormLayout(self.Qballooning_widget)
        self.Qfit_button = QtGui.QPushButton('modify with handles')

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
        self.Qballooning_widget.setWindowTitle('ballooning')
        self.Qballooning_layout.addWidget(self.Qballooning_name)
        self.Qballooning_layout.addWidget(self.Qfit_button)

        # selection widget
        self.layout.addWidget(self.QList_View)
        for ballooning in self.parametric_glider.balloonings:
            self.QList_View.addItem(QBalooning(ballooning, scale_y=self.scale_y))
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

        self.spline_select = spline_select([], self.update_degree)
        self.layout.addWidget(self.spline_select)

    def setup_pivy(self):
        self.task_separator += [self.ballooning_sep, self.spline_sep]
        self.update_selection()
        self.grid = coin.SoSeparator()
        self.task_separator += [self.grid]
        self._update_grid()
        Gui.SendMsgToActiveView('ViewFit')
        self.insert_cb = self.view.addEventCallbackPivy(coin.SoKeyboardEvent.getClassTypeId(), self.insert_point)

    def _update_grid(self, grid_x=None, grid_y=None):
        grid_x = grid_x or numpy.linspace(0., 1., int(20 + 1))
        grid_y = grid_y or numpy.linspace(-0.1*self.scale_y, 0.1*self.scale_y, int(20 + 1))
        self.grid.removeAllChildren()
        x_points_lower = [[x, grid_y[0], -0.001] for x in grid_x]
        x_points_upper = [[x, grid_y[-1], -0.001] for x in grid_x]
        y_points_lower = [[grid_x[0], y, -0.001] for y in grid_y if y != 0]
        y_points_upper = [[grid_x[-1], y, -0.001] for y in grid_y if y != 0]
        for l in zip(x_points_lower, x_points_upper):
            self.grid += [Line(l, color='grey').object]
        for l in zip(y_points_lower, y_points_upper):
            self.grid += [Line(l, color='grey').object]

        self.grid += (Line([[0, 0, -0.001], [1,0,-0.001]], color="red").object, )
        for l in y_points_upper[::10]:
            textsep = coin.SoSeparator()
            text = coin.SoText2()
            trans = coin.SoTranslation()
            trans.translation = l
            text.string = str(l[1])
            textsep += [trans, textsep, text]

    def create_ballooning(self):
        j = 0
        for index in range(self.QList_View.count()):
            name = self.QList_View.item(index).text()
            if 'ballooning' in name:
                j += 1
        ballooning = BallooningBezier()
        ballooning.name = "ballooning" + str(j)
        new_item = QBalooning(ballooning, scale_y=self.scale_y)
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
        self.ballooning_sep += [self.upper_spline]
        self.ballooning_sep += [self.lower_spline]

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
            self.upper_cpc.grid = [0.01, 0.01, 100]
            self.lower_cpc = ControlPointContainer(view=self.view)
            self.lower_cpc.grid = [0.01, 0.01, 100]
            self.upper_cpc.control_pos = self.current_ballooning.upper_controlpoints
            self.lower_cpc.control_pos = self.current_ballooning.lower_controlpoints
            # self.upper_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[-1].fix = True
            self.lower_cpc.control_points[0].fix = True
            # self.upper_cpc.control_points[0].fix = True
            self.spline_sep += [self.upper_cpc, self.lower_cpc]
            self.spline_sep += [self.lower_spline, self.upper_spline]
            self.upper_cpc.on_drag.append(self.upper_on_change)
            self.lower_cpc.on_drag.append(self.lower_on_change)
            self.upper_cpc.drag_release.append(self.upper_drag_release)
            self.lower_cpc.drag_release.append(self.lower_drag_release)
            self.upper_drag_release()
            self.lower_drag_release()
            self.spline_select.spline_objects = [self.current_ballooning.ballooning.upper_spline, 
                                                 self.current_ballooning.ballooning.lower_spline]

    def update_degree(self, *args):
        if self.current_ballooning is not None and self.is_edit:
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
        self.upper_cpc.control_points[-1].set_x(1.)
        self.upper_cpc.control_points[0].set_x(0.)
        self.lower_cpc.control_points[-1].set_y(-self.upper_cpc.control_points[-1].pos[1])
        self.lower_cpc.control_points[0].set_y(-self.upper_cpc.control_points[0].pos[1])
        self.current_ballooning.upper_controlpoints = [
            i[:-1] for i in self.upper_cpc.control_pos]
        self.draw_upper_spline(num)
        self._update_lower_spline(num)

    def draw_upper_spline(self, num):
        self.upper_spline.removeAllChildren()
        l = Line(vector3D(self.current_ballooning.get_expl_upper_spline(num)),
                 color='red', width=2)
        self.upper_spline += [l.object]

    def _update_lower_spline(self, num):
        self.current_ballooning.lower_controlpoints = [
            i[:-1] for i in self.lower_cpc.control_pos]
        self.draw_lower_spline(num)

    def draw_lower_spline(self, num):
        self.lower_spline.removeAllChildren()
        l = Line(vector3D(self.current_ballooning.get_expl_lower_spline(num)),
                 color='red', width=2)
        self.lower_spline += [l.object]

    def insert_point(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord('i')):
            if not self.is_edit:
                return
            if event.getState() == event.DOWN:
                pos = list(self.view.getPoint(*event.getPosition()))[0:2]
                self.unset_edit_mode()
                if pos[1] > 0:
                    insert_point(self.current_ballooning.upper_controlpoints, pos)
                    # self.current_ballooning.upper_controlpoints = insert_point(
                    #     self.current_ballooning.upper_controlpoints, pos)
                else:
                    insert_point(self.current_ballooning.upper_controlpoints, pos)
                    # self.current_ballooning.lower_controlpoints = insert_point(
                    #     self.current_ballooning.lower_controlpoints, pos)
                self.current_ballooning.apply_splines()
                self.set_edit_mode()


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
        for index in range(self.QList_View.count()):
            ballooning = self.QList_View.item(index)
            ballooning.apply_splines()
            balloonings.append(ballooning.ballooning)
        self.parametric_glider.balloonings = balloonings
        self.update_view_glider()
        super(BallooningTool, self).accept()


class QBalooning(QtGui.QListWidgetItem):
    def __init__(self, ballooning, scale_y=10):
        self.ballooning = ballooning
        super(QBalooning, self).__init__()
        self.setText(self.ballooning.name)
        self.scale_y = scale_y
        self.upper_controlpoints = numpy.array([1., self.scale_y]) * self.ballooning.upper_spline.controlpoints
        self.lower_controlpoints = numpy.array([1., -self.scale_y]) * self.ballooning.lower_spline.controlpoints
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

    def get_expl_lower_spline(self, num):
        # self.apply_splines()
        self.ballooning.lower_spline.controlpoints = self.lower_controlpoints * numpy.array([1., -1./self.scale_y])
        seq = self.ballooning.lower_spline.get_sequence(num)
        return seq * numpy.array([1., -self.scale_y])

    def get_expl_upper_spline(self, num):
        # self.apply_splines()
        self.ballooning.upper_spline.controlpoints = self.upper_controlpoints * numpy.array([1., 1./self.scale_y])
        seq = self.ballooning.upper_spline.get_sequence(num)
        return seq * numpy.array([1., self.scale_y])

    def apply_splines(self):
        self.ballooning.controlpoints = [
            numpy.array([1., 1./self.scale_y])*self.upper_controlpoints,
            numpy.array([1., -1./self.scale_y])*self.lower_controlpoints
        ]

def insert_point(points, insert_point):
    forward = points[-1][0] > points[0][0]
    for i, point in enumerate(points):
        if (point[0] < insert_point[0]) == forward:
            pass
        else:
            break
    points.insert(i, insert_point)
    return points