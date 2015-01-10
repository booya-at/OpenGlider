from __future__ import division

from PySide import QtCore, QtGui
from pivy import coin
import numpy
import FreeCADGui as Gui
from openglider.airfoil.parametric import BezierProfile2D

from openglider.jsonify import dump, load
from openglider.glider.glider_2d import Glider2D
from openglider.utils.bezier import fitbezier
from openglider.vector import norm, normalize
from pivy_primitives import Line, vector3D, ControlPointContainer


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
            glider.glider_2d.glider_3d(glider.glider_instance)
            glider.ViewObject.Proxy.updateData()

class base_tool(object):

    def __init__(self, obj, widget_name="base_widget"):
        self.obj = obj
        if self.obj.glider_2d.parametric:
            self.glider_2d = self.obj.glider_2d
            print(self.glider_2d)
        else:
            print('fit the glider')
            self.glider_2d = Glider2D.fit_glider(self.obj.glider_instance)
        self.obj.ViewObject.Visibility = False
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


class shape_tool(base_tool):

    def __init__(self, obj):
        super(shape_tool, self).__init__(obj, widget_name="shape tool")

        # scene components
        self.shape = coin.SoSeparator()
        self.front_cpc = ControlPointContainer(vector3D(self.glider_2d.front.controlpoints), self.view)
        self.back_cpc = ControlPointContainer(vector3D(self.glider_2d.back.controlpoints), self.view)
        self.rib_pos_cpc = ControlPointContainer(vector3D(self.glider_2d.cell_dist_controlpoints), self.view)

        # form components
        # self.Qmanual_edit = QtGui.QCheckBox(self.base_widget)
        self.Qnum_front = QtGui.QSpinBox(self.base_widget)
        self.Qnum_back = QtGui.QSpinBox(self.base_widget)
        self.Qnum_dist = QtGui.QSpinBox(self.base_widget)
        self.Qnum_cells = QtGui.QSpinBox(self.base_widget)
        # self.Qcheck1 = QtGui.QCheckBox(self.base_widget)
        self.Qset_const = QtGui.QPushButton(self.base_widget)

        self.setup_widget()
        self.setup_pivy()
        Gui.SendMsgToActiveView("ViewFit")

    def accept(self):
        self.glider_2d.glider_3d(self.obj.glider_instance)
        self.obj.glider_2d = self.glider_2d
        self.obj.ViewObject.Proxy.updateData()
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.rib_pos_cpc.remove_callbacks()
        super(shape_tool, self).accept()

    def reject(self):
        self.back_cpc.remove_callbacks()
        self.front_cpc.remove_callbacks()
        self.rib_pos_cpc.remove_callbacks()
        super(shape_tool, self).reject()

    def setup_widget(self):
        self.Qnum_cells.setValue(int(self.glider_2d.cell_num))
        self.Qnum_front.setValue(len(self.glider_2d.front.controlpoints))
        self.Qnum_back.setValue(len(self.glider_2d.back.controlpoints))
        self.Qnum_dist.setValue(len(self.glider_2d.cell_dist_controlpoints))
        # self.base_widget.connect(self.Qmanual_edit, QtCore.SIGNAL('stateChanged(int)'), self.line_edit)
        # self.base_widget.connect(self.Qcheck1, QtCore.SIGNAL('stateChanged(int)'), self.rib_edit)
        self.base_widget.connect(self.Qnum_cells, QtCore.SIGNAL('valueChanged(int)'), self.update_num_cells)
        self.base_widget.connect(self.Qset_const, QtCore.SIGNAL('clicked()'), self.update_const)
        self.base_widget.connect(self.Qnum_dist, QtCore.SIGNAL('valueChanged(int)'), self.update_num_dist)
        self.base_widget.connect(self.Qnum_back, QtCore.SIGNAL('valueChanged(int)'), self.update_num_back)
        self.base_widget.connect(self.Qnum_front, QtCore.SIGNAL('valueChanged(int)'), self.update_num_front)

        self.Qnum_cells.setMaximum(150)
        self.Qnum_back.setMaximum(5)
        self.Qnum_front.setMaximum(5)
        self.Qnum_dist.setMaximum(5)

        self.Qnum_cells.setMinimum(10)
        self.Qnum_back.setMinimum(2)
        self.Qnum_front.setMinimum(2)
        self.Qnum_dist.setMinimum(1)

        # self.layout.setWidget(1, text_field, QtGui.QLabel("manual shape edit"))
        # self.layout.setWidget(1, input_field, self.Qmanual_edit)
        self.layout.setWidget(2, text_field, QtGui.QLabel("front num_points"))
        self.layout.setWidget(2, input_field, self.Qnum_front)
        self.layout.setWidget(3, text_field, QtGui.QLabel("back num_points"))
        self.layout.setWidget(3, input_field, self.Qnum_back)
        # self.layout.setWidget(4, text_field, QtGui.QLabel("manual cell pos"))
        # self.layout.setWidget(4, input_field, self.Qcheck1)
        self.layout.setWidget(5, text_field, QtGui.QLabel("num_cells"))
        self.layout.setWidget(5, input_field, self.Qnum_cells)
        self.layout.setWidget(6, text_field, QtGui.QLabel("dist num_points"))
        self.layout.setWidget(6, input_field, self.Qnum_dist)
        self.layout.setWidget(7, text_field, QtGui.QLabel("constant AR"))
        self.layout.setWidget(7, input_field, self.Qset_const)

    def setup_pivy(self):
        # setting on drag behavior
        self.front_cpc.on_drag.append(self.update_data_back)
        self.back_cpc.on_drag.append(self.update_data_front)
        self.rib_pos_cpc.on_drag.append(self.update_shape)

        # adding graphics to the main separator
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.front_cpc)
        self.task_separator.addChild(self.back_cpc)
        self.task_separator.addChild(self.rib_pos_cpc)
        self.update_shape()

    def line_edit(self):
        self.front_cpc.set_edit_mode(self.view)
        self.back_cpc.set_edit_mode(self.view)

    def rib_edit(self):
        self.rib_pos_cpc.set_edit_mode(self.view)
        self.update_shape()

    def update_num_dist(self, val):
        self.glider_2d.cell_dist.numpoints = val + 2
        self.rib_pos_cpc.control_pos = vector3D(self.glider_2d.cell_dist._controlpoints[1:-1])
        self.update_shape()

    def update_num_front(self, val):
        self.glider_2d.front.numpoints = val
        self.front_cpc.control_pos = vector3D(self.glider_2d.front.controlpoints)
        self.update_shape()

    def update_num_back(self, val):
        self.glider_2d.back.numpoints = val
        self.back_cpc.control_pos = vector3D(self.glider_2d.back.controlpoints)
        self.update_shape()

    def update_data_back(self):
        self.back_cpc.control_points[-1].set_x(self.front_cpc.control_points[-1].pos[0])
        self.update_shape()

    def update_data_front(self):
        self.front_cpc.control_points[-1].set_x(self.back_cpc.control_points[-1].pos[0])
        self.update_shape()

    def update_num_cells(self, val):
        self.glider_2d.cell_num = val
        self.update_shape()

    def update_const(self):
        const_dist = self.glider_2d.depth_integrated()
        self.glider_2d.cell_dist.controlpoints = fitbezier(const_dist, self.glider_2d.cell_dist._bezierbase)
        self.rib_pos_cpc.control_pos = self.glider_2d.cell_dist_controlpoints
        self.update_shape()

    def update_shape(self, arg=None, num=30):
        self.glider_2d.front.controlpoints = [i[:-1] for i in self.front_cpc.control_pos]
        self.glider_2d.back.controlpoints = [i[:-1] for i in self.back_cpc.control_pos]
        self.glider_2d.cell_dist_controlpoints = [i[:-1] for i in self.rib_pos_cpc.control_pos]
        self.shape.removeAllChildren()
        ribs, front, back = self.glider_2d.shape(num=15)
        dist_line = self.glider_2d.cell_dist_interpolation
        self.shape.addChild(Line(front).object)
        self.shape.addChild(Line(back).object)
        for rib in ribs:
            self.shape.addChild(Line(rib).object)
        self.shape.addChild(Line(dist_line).object)
        for i in dist_line:
            self.shape.addChild(Line([[0, i[1]], i, [i[0], 0]], color="gray").object)


class arc_tool(base_tool):

    def __init__(self, obj):
        """adds a symmetric spline to the scene"""
        super(arc_tool, self).__init__(obj, widget_name="arc_tool")

        self.arc_cpc = ControlPointContainer(self.glider_2d.arc.controlpoints, self.view)
        # self.Qmanual_edit = QtGui.QCheckBox(self.base_widget)
        self.Qnum_arc = QtGui.QSpinBox(self.base_widget)
        # self.Qcalc_real = QtGui.QPushButton(self.base_widget)
        self.shape = coin.SoSeparator()
        self.task_separator.addChild(self.shape)

        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):

        self.Qnum_arc.setMaximum(5)
        self.Qnum_arc.setMinimum(2)
        self.Qnum_arc.setValue(len(self.glider_2d.arc.controlpoints))
        self.glider_2d.arc.numpoints = self.Qnum_arc.value()

        # self.layout.setWidget(1, text_field, QtGui.QLabel("manual arc edit"))
        # self.layout.setWidget(1, input_field, self.Qmanual_edit)
        self.layout.setWidget(2, text_field, QtGui.QLabel("arc num_points"))
        self.layout.setWidget(2, input_field, self.Qnum_arc)
        # self.layout.setWidget(3, text_field, QtGui.QLabel("calculate real arc"))
        # self.layout.setWidget(3, input_field, self.Qcalc_real)

        # self.base_widget.connect(self.Qmanual_edit, QtCore.SIGNAL("stateChanged(int)"), self.set_edit)
        self.base_widget.connect(self.Qnum_arc, QtCore.SIGNAL("valueChanged(int)"), self.update_num)

    def setup_pivy(self):
        self.arc_cpc.on_drag.append(self.update_spline)
        self.arc_cpc.drag_release.append(self.update_real_arc)
        self.task_separator.addChild(self.arc_cpc)
        self.shape.addChild(Line(self.glider_2d.arc.get_sequence(num=30), color="red").object)
        self.shape.addChild(Line(self.glider_2d.arc_pos()).object)

    # def set_edit(self, *arg):
    #     self.arc_cpc.set_edit_mode(self.view)

    def update_spline(self):
        self.shape.removeAllChildren()
        self.glider_2d.arc.controlpoints = [i[:-1] for i in self.arc_cpc.control_pos]
        self.shape.addChild(Line(self.glider_2d.arc.get_sequence(num=30), color="red").object)

    def update_real_arc(self):
        self.shape.addChild(Line(self.glider_2d.arc_pos()).object)

    def update_num(self, *arg):
        self.glider_2d.arc.numpoints = self.Qnum_arc.value()
        self.arc_cpc.control_pos = self.glider_2d.arc.controlpoints
        self.update_spline()

    def accept(self):
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.glider_3d(self.obj.glider_instance)
        self.arc_cpc.remove_callbacks()
        self.obj.ViewObject.Proxy.updateData()
        super(arc_tool, self).accept()

    def reject(self):
        self.arc_cpc.remove_callbacks()
        super(arc_tool, self).reject()


class aoa_tool(base_tool):

    def __init__(self, obj):
        # TODO:
        # -maybe create a abase class for this kind of inputs.
        #       so that the z-rot-tool can erb from this

        # BASE-VALUE-TOOL
        # -coord system that can be scaled(drag the y-axis-arrow)
        # -values on the y axis (SoText2())
        # -values of the ribs (release drag)

        # AOA-TOOL
        # -add a spinbox for the glideratio
        # -show the absolute value of the angle (release drag)
        # -switcher to change between relativ absolute inputs

        super(aoa_tool, self).__init__(obj)
        self.scale = numpy.array([1., 5.])
        self.aoa_cpc = ControlPointContainer(vector3D(numpy.array(self.glider_2d.aoa.controlpoints) * self.scale), self.view)
        self.shape = coin.SoSeparator()
        self.coords = coin.SoSeparator()
        self.aoa_spline = Line([])
        self.ribs, self.front, self.back = self.glider_2d.shape()

        self.aoa_cpc.on_drag.append(self.update_aoa)
        self.setup_pivy()

    def setup_pivy(self):
        self.aoa_cpc.control_points[-1].constraint = lambda pos: [self.glider_2d.span / 2, pos[1], pos[2]]
        self.task_separator.addChild(self.aoa_cpc)
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.aoa_spline.object)
        self.task_separator.addChild(self.coords)
        self.update_aoa()
        self.draw_shape()

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.front, color="gray").object)
        self.shape.addChild(Line(self.back, color="gray").object)
        for rib in self.ribs:
            self.shape.addChild(Line(rib, color="gray").object)

    def update_aoa(self):
        self.glider_2d.aoa.controlpoints = (numpy.array([i[:-1] for i in self.aoa_cpc.control_pos]) / self.scale).tolist()
        self.aoa_spline.update(self.glider_2d.aoa.get_sequence(num=20) * self.scale)
        self.coords.removeAllChildren()
        max_x = max([i[0] for i in self.aoa_cpc.control_pos])
        max_y = max([i[1] for i in self.aoa_cpc.control_pos])
        self.coords.addChild(Line([[0, 0], [0., max_y]]).object)
        self.coords.addChild(Line([[0, 0], [max_x, 0.]]).object)

    def accept(self):
        self.aoa_cpc.remove_callbacks()
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.glider_3d(self.obj.glider_instance)
        super(aoa_tool, self).accept()

    def reject(self):
        self.aoa_cpc.remove_callbacks()
        super(aoa_tool, self).reject()


class base_merge_tool(base_tool):
    # imagine you have a list of input data. (profiles, ballooning, etc...). this tool should provide a methode to distribute this
    # input data to the ribs.
    # all data list
    # selected data = data to distribute

    def __init__(self, obj):
        super(base_merge_tool, self).__init__(obj)
        self.dist_list = []

    def setup_widget(self):
        # 1 show a list of all possibilities (selectabel) (spinbox)
        # 2 button to include one of thise items
        # 3 in a second list (items in a table)
        # 4 wich is sortable (button up button down)
        pass


class ballooning_merge(base_merge_tool):
    pass


class airfoil_merge(base_merge_tool):
    pass


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

        #connections
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
            self.QList_View.addItem(QAirfoil_item(BezierProfile2D.import_from_dat(filename[0])))

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
        print(self.current_airfoil)
        self.airfoil_sep.addChild(Line(vector3D(self.current_airfoil)).object)

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

    def _draw_spline(self, num):
        self.upper_spline.addChild(Line(vector3D(self.current_airfoil.upper_spline.controlpoints), color="gray").object)
        self.upper_spline.addChild(Line(vector3D(self.current_airfoil.upper_spline.get_sequence(num))).object)
        self.lower_spline.addChild(Line(vector3D(self.current_airfoil.lower_spline.controlpoints), color="gray").object)
        self.lower_spline.addChild(Line(vector3D(self.current_airfoil.lower_spline.get_sequence(num))).object)

    def _update_upper_spline(self, num=20):
        self.upper_spline.removeAllChildren()
        self.lower_spline.removeAllChildren()
        self.current_airfoil.upper_spline.controlpoints =[i[:-1] for i in self.upper_cpc.control_pos]
        direction = normalize(self.current_airfoil.upper_spline.controlpoints[-2])
        radius = norm(self.current_airfoil.lower_spline.controlpoints[1])
        new_point = - numpy.array(direction) * radius
        self.current_airfoil.lower_spline.controlpoints[1] = new_point
        self.lower_cpc.control_points[1].pos = vector3D(new_point)
        self._draw_spline(num)

    def _update_lower_spline(self, num=20):
        self.lower_spline.removeAllChildren()
        self.upper_spline.removeAllChildren()
        self.current_airfoil.lower_spline.controlpoints =[i[:-1] for i in self.lower_cpc.control_pos]
        direction = normalize(self.current_airfoil.lower_spline.controlpoints[1])
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
            profiles.append(airfoil)
        self.glider_2d.profiles = profiles
        self.obj.glider_2d = self.glider_2d
        super(airfoil_tool, self).accept()


class QAirfoil_item(QtGui.QListWidgetItem):
    def __init__(self, airfoil):
        self.airfoil = airfoil
        super(QAirfoil_item, self).__init__()
        self.setText(self.airfoil.name)
