from __future__ import division
from PySide import QtCore, QtGui
from pivy import coin
import numpy
import FreeCADGui as Gui
import FreeCAD
from pivy_primitives import Line, vector3D, ControlPointContainer, Marker
from openglider.glider.glider import Glider_2D
from openglider.utils.bezier import fitbezier

text_field = QtGui.QFormLayout.LabelRole
input_field = QtGui.QFormLayout.FieldRole

# TODO: 
#   -merge-tool
#       -airfoil
#       -ballooning
#       -aoa
#       -zrot
#   -airfoil-tool
#   -ballooning-tool
#   -attachmentpoint-tool
#   -line-tool
#   -inlet-tool
#   -design-tool
#   -minirips-tool
#   -etc...


class base_tool(object):
    def __init__(self, obj, widget_name="base_widget"):
        self.obj = obj
        if self.obj.glider_2d.parametric:
            self.glider_2d = self.obj.glider_2d
        else:
            print('fit the glider')
            self.glider_2d = Glider_2D.fit_glider(self.obj.glider_instance)
        self.obj.ViewObject.Visibility = False
        Gui.activeDocument().activeView().viewTop()
        self.view = Gui.ActiveDocument.ActiveView
        self.scene = self.view.getSceneGraph()
        self.nav_bak = self.view.getNavigationType()
        self.view.setNavigationType('Gui::TouchpadNavigationStyle')

        # form is the widget that appears in the task panel,
        self.form = []

        self.base_widget = QtGui.QWidget()
        self.form.append(self.base_widget)
        self.layout = QtGui.QFormLayout(self.base_widget)
        self.base_widget.setWindowTitle(widget_name)

        # scene container
        self.task_separator = coin.SoSeparator()
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


class shape_tool(base_tool):
    def __init__(self, obj):
        super(shape_tool, self).__init__(obj, widget_name="shape tool")

        # scene components
        self.shape = coin.SoSeparator()
        self.front_cpc = ControlPointContainer(vector3D(self.glider_2d.front.controlpoints))
        self.back_cpc = ControlPointContainer(vector3D(self.glider_2d.back.controlpoints))
        self.rib_pos_cpc = ControlPointContainer(vector3D(self.glider_2d.cell_dist_controlpoints))

        # form components
        self.Qmanual_edit = QtGui.QCheckBox(self.base_widget)
        self.Qnum_front = QtGui.QSpinBox(self.base_widget)
        self.Qnum_back = QtGui.QSpinBox(self.base_widget)
        self.Qnum_dist = QtGui.QSpinBox(self.base_widget)
        self.Qnum_cells = QtGui.QSpinBox(self.base_widget)
        self.Qcheck1 = QtGui.QCheckBox(self.base_widget)
        self.Qset_const = QtGui.QPushButton(self.base_widget)

        self.setup_widget()
        self.setup_pivy()
        Gui.SendMsgToActiveView("ViewFit")

    def accept(self):
        self.glider_2d.glider_3d(self.obj.glider_instance)
        self.obj.glider_2d = self.glider_2d
        self.obj.ViewObject.Proxy.updateData()
        self.back_cpc.unset_edit_mode()
        self.front_cpc.unset_edit_mode()
        self.rib_pos_cpc.unset_edit_mode()
        super(shape_tool, self).accept()

    def reject(self):
        self.back_cpc.unset_edit_mode()
        self.front_cpc.unset_edit_mode()
        self.rib_pos_cpc.unset_edit_mode()
        super(shape_tool, self).reject()

    def setup_widget(self):
        self.Qnum_cells.setValue(int(self.glider_2d.cell_num))
        self.Qnum_front.setValue(len(self.glider_2d.front.controlpoints))
        self.Qnum_back.setValue(len(self.glider_2d.back.controlpoints))
        self.Qnum_dist.setValue(len(self.glider_2d.cell_dist_controlpoints))
        self.base_widget.connect(self.Qmanual_edit, QtCore.SIGNAL('stateChanged(int)'), self.line_edit)
        self.base_widget.connect(self.Qcheck1, QtCore.SIGNAL('stateChanged(int)'), self.rib_edit)
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


        self.layout.setWidget(1, text_field, QtGui.QLabel("manual shape edit"))
        self.layout.setWidget(1, input_field, self.Qmanual_edit)
        self.layout.setWidget(2, text_field, QtGui.QLabel("front num_points"))
        self.layout.setWidget(2, input_field, self.Qnum_front)
        self.layout.setWidget(3, text_field, QtGui.QLabel("back num_points"))
        self.layout.setWidget(3, input_field, self.Qnum_back)
        self.layout.setWidget(4, text_field, QtGui.QLabel("manual cell pos"))
        self.layout.setWidget(4, input_field, self.Qcheck1)
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
        self.rib_pos_cpc.set_control_points(vector3D(self.glider_2d.cell_dist._controlpoints[1:-1]))
        self.update_shape()

    def update_num_front(self, val):
        self.glider_2d.front.numpoints = val
        self.front_cpc.set_control_points(vector3D(self.glider_2d.front.controlpoints))
        self.update_shape()

    def update_num_back(self, val):
        self.glider_2d.back.numpoints = val
        self.back_cpc.set_control_points(vector3D(self.glider_2d.back.controlpoints))
        self.update_shape()

    def update_data_back(self):
        self.back_cpc.control_points[-1].set_x(self.front_cpc.control_points[-1].x)
        self.update_shape()

    def update_data_front(self):
        self.front_cpc.control_points[-1].set_x(self.back_cpc.control_points[-1].x)
        self.update_shape()

    def update_num_cells(self, val):
        self.glider_2d.cell_num = val
        self.update_shape()

    def update_const(self):
        const_dist = self.glider_2d.depth_integrated()
        self.glider_2d.cell_dist.controlpoints = fitbezier(const_dist, self.glider_2d.cell_dist._bezierbase)
        self.rib_pos_cpc.set_control_points(self.glider_2d.cell_dist_controlpoints)
        self.update_shape()

    def update_shape(self, arg=None, num=30):
        self.glider_2d.front.controlpoints = [i[:-1] for i in self.front_cpc.control_point_list]
        self.glider_2d.back.controlpoints = [i[:-1] for i in self.back_cpc.control_point_list]
        self.glider_2d.cell_dist_controlpoints = [i[:-1] for i in self.rib_pos_cpc.control_point_list]
        self.shape.removeAllChildren()
        ribs, front, back, dist_line = self.glider_2d.interactive_shape(num=15)
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

        self.arc_cpc = ControlPointContainer(self.glider_2d.arc.controlpoints)
        self.Qmanual_edit = QtGui.QCheckBox(self.base_widget)
        self.Qnum_arc = QtGui.QSpinBox(self.base_widget)
        self.Qcalc_real =QtGui.QPushButton(self.base_widget)
        self.shape = coin.SoSeparator()
        self.task_separator.addChild(self.shape)

        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):

        self.Qnum_arc.setMaximum(5)
        self.Qnum_arc.setMinimum(2)
        self.Qnum_arc.setValue(len(self.glider_2d.arc.controlpoints))
        self.glider_2d.arc.numpoints = self.Qnum_arc.value()

        self.layout.setWidget(1, text_field, QtGui.QLabel("manual arc edit"))
        self.layout.setWidget(1, input_field, self.Qmanual_edit)
        self.layout.setWidget(2, text_field, QtGui.QLabel("arc num_points"))
        self.layout.setWidget(2, input_field, self.Qnum_arc)
        self.layout.setWidget(3, text_field, QtGui.QLabel("calculate real arc"))
        self.layout.setWidget(3, input_field, self.Qcalc_real)

        self.base_widget.connect(self.Qmanual_edit, QtCore.SIGNAL("stateChanged(int)"), self.set_edit)
        self.base_widget.connect(self.Qnum_arc, QtCore.SIGNAL("valueChanged(int)"), self.update_num)
        self.base_widget.connect(self.Qcalc_real, QtCore.SIGNAL("clicked()"), self.real_arc)

    def setup_pivy(self):
        self.arc_cpc.on_drag.append(self.update_spline)
        self.task_separator.addChild(self.arc_cpc)
        self.shape.addChild(Line(self.glider_2d.arc.get_sequence(num=20).T, color="red").object)
        self.shape.addChild(Line(self.glider_2d.arc_pos()).object)

    def set_edit(self, *arg):
        self.arc_cpc.set_edit_mode(self.view)

    def update_spline(self):
        self.shape.removeAllChildren()
        self.glider_2d.arc.controlpoints = [i[:-1] for i in self.arc_cpc.control_point_list]
        self.shape.addChild(Line(self.glider_2d.arc.get_sequence(num=20).T, color="red").object)
        self.shape.addChild(Line(self.glider_2d.arc_pos()).object)

    def update_num(self, *arg):
        self.glider_2d.arc.numpoints = self.Qnum_arc.value()
        self.arc_cpc.set_control_points(self.glider_2d.arc.controlpoints)
        self.update_spline()

    def real_arc(self):
        pass

    def accept(self):
        self.obj.glider_2d = self.glider_2d
        self.glider_2d.glider_3d(self.obj.glider_instance)
        self.arc_cpc.unset_edit_mode()
        self.obj.ViewObject.Proxy.updateData()
        super(arc_tool, self).accept()

    def reject(self):
        self.arc_cpc.unset_edit_mode()
        super(arc_tool, self).reject()


class base_point_tool(base_tool):
    def __init__(self, obj):
        # allow helper curves
        # callback for point visualization (only when mouse near a cutting point)
        super(base_point_tool, self).__init__(obj, widget_name="airfoil tool")

        #save the shape as it will not be changed in this task
        self.ribs, self.front, self.back = self.glider_2d.shape()
        self.xpos = [i[0] for i in self.front]
        self.current_point = None

        #adding some pivy containers
        self.shape = coin.SoSeparator()
        self.helper_line = coin.SoSeparator()
        self.temp_point = coin.SoSeparator()
        self.vis_point_list = coin.SoSeparator()
        self.__point_list = []  # glider 2d should store these points (overwrite update_point_list)
        self.setup_pivy()

        #qt gui stuff
        self.Qhelper_lines = QtGui.QWidget()
        self.Qhl_layout = QtGui.QFormLayout(self.Qhelper_lines)
        self.Qhl_pos = QtGui.QDoubleSpinBox(self.Qhelper_lines)
        self.setup_widget()

    def setup_pivy(self):
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.helper_line)
        self.task_separator.addChild(self.temp_point)
        self.task_separator.addChild(self.vis_point_list)
        self.draw_shape()
        self.update_helper_line()
        self.setup_cb()

    def setup_widget(self):
        self.form.append(self.Qhelper_lines)
        self.Qhl_pos.setValue(50)
        self.Qhl_pos.setRange(0, 100)
        self.Qhl_pos.setSingleStep(1)

        self.Qhelper_lines.connect(self.Qhl_pos, QtCore.SIGNAL('valueChanged(double)'), self.update_helper_line)

        self.Qhl_layout.setWidget(1, text_field, QtGui.QLabel("helper_line_pos"))
        self.Qhl_layout.setWidget(1, input_field, self.Qhl_pos)

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.front).object)
        self.shape.addChild(Line(self.back).object)
        for rib in self.ribs:
            self.shape.addChild(Line(rib).object)

    def update_helper_line(self, pos=50):
        self.helper_line.removeAllChildren()
        self.helper_line.addChild(Line(self.help_line(pos / 100), color="red").object)

    # chached
    def help_line(self, pos=0.5):
        return [fr + pos * (ba - fr) for fr, ba in numpy.array(self.ribs)]

    def setup_cb(self):
        print("blaassdkj")
        self.point_preview_cb = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.point_preview)
        self.add_point_cb = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.add_point)

    def remove_cb(self):
        if self.point_preview_cb:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.point_preview_cb)
        if self.add_point_cb:
            self.view.removeEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.add_point_cb)

    def point_preview(self, event_callback):        
        event = event_callback.getEvent()
        self.temp_point.removeAllChildren()
        if type(event) == coin.SoLocation2Event:
            self.current_point = None
            pos = event.getPosition()
            if event.wasCtrlDown():
                check_points = self.__point_list
                color = "green"
            else:
                check_points = self.help_line(self.Qhl_pos.value() / 100)
                color = "red"
            for point in check_points:
                s = self.view.getPointOnScreen(point[0], point[1], 0.)
                if (abs(s[0] - pos[0]) ** 2 + abs(s[1] - pos[1]) ** 2) < (15 ** 2) and point[0] >= 0:
                    self.current_point = point
                    self.temp_point.addChild(Marker([point], color=color))
                    break

    def update_point_list(self):
        self.vis_point_list.removeAllChildren()
        if len(self.__point_list) > 0:
            self.vis_point_list.addChild(Marker(self.__point_list))

    def add_point(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        if self.current_point is not None and event.getState():
            if event.wasCtrlDown(): # deleting current point
                print(self.current_point in self.__point_list)
                try:
                    self.__point_list.remove(self.current_point)
                    self.current_point = None
                    self.temp_point.removeAllChildren()
                    self.update_point_list()
                except ValueError:
                    print("whats wrong here???")
            else: # adding a point
                print("add point")
                self.__point_list.append(self.current_point)
                self.update_point_list()



    def accept(self):
        self.remove_cb()
        super(base_point_tool, self).accept()

    def reject(self):
        self.remove_cb()
        super(base_point_tool, self).reject()


class aoa_tool(base_tool):
    def __init__(self, obj):
        super(aoa_tool, self).__init__(obj)
        self.scale = numpy.array([1., 5.])
        self.aoa_cpc = ControlPointContainer(vector3D(numpy.array(self.glider_2d.aoa.controlpoints) * self.scale))
        self.shape = coin.SoSeparator()
        self.aoa_spline = Line([])
        self.ribs, self.front, self.back = self.glider_2d.shape()

        self.aoa_cpc.on_drag.append(self.update_aoa)
        self.setup_pivy()
        self.aoa_cpc.set_edit_mode(self.view)

    def setup_pivy(self):
        self.task_separator.addChild(self.aoa_cpc)
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.aoa_spline.object)
        self.update_aoa()
        self.draw_shape()

    def draw_shape(self):
        self.shape.removeAllChildren()
        self.shape.addChild(Line(self.front, color="gray").object)
        self.shape.addChild(Line(self.back, color="gray").object)
        for rib in self.ribs:
            self.shape.addChild(Line(rib, color="gray").object)

    def update_aoa(self):
        self.glider_2d.aoa.controlpoints = (numpy.array([i[:-1] for i in self.aoa_cpc.control_point_list]) / self.scale).tolist()
        self.aoa_spline.update(self.glider_2d.aoa.get_sequence(num=20).T * self.scale)
