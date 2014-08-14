from PySide import QtCore, QtGui
from pivy import coin
import FreeCADGui as Gui
from pivy_primitives import Line, vector3D, ControlPointContainer
from openglider.glider.glider import Glider_2D
from openglider.utils.bezier import fitbezier

text_field = QtGui.QFormLayout.LabelRole
input_field = QtGui.QFormLayout.FieldRole

class base_tool(object):
    def __init__(self, obj, widget_name="base_widget"):
        self.obj = obj
        self.obj.ViewObject.Visibility = False
        self.view = Gui.ActiveDocument.ActiveView
        self.scene = self.view.getSceneGraph()

        # form is the widget that appears in the task panel,
        self.base_widget = QtGui.QWidget()
        self.form = [self.base_widget]
        self.layout = QtGui.QFormLayout(self.base_widget)
        self.base_widget.setWindowTitle(widget_name)

        # scene container
        self.task_separator = coin.SoSeparator()
        self.scene.addChild(self.task_separator)

    def accept(self):
        self.obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()

    def reject(self):
        self.obj.ViewObject.Visibility = True
        self.scene.removeChild(self.task_separator)
        Gui.Control.closeDialog()


class shape_tool(base_tool):
    def __init__(self, obj):
        super(shape_tool, self).__init__(obj, widget_name="shape tool")
        self.glider_copy = self.obj.glider_instance.copy_complete()
        self.glider_2d = Glider_2D.fit_glider(self.obj.glider_instance)
        self.shape = None
        self.front_cpc = None
        self.back_cpc = None
        self.rib_pos_cpc = None
        self.line1 = None
        self.line2 = None
        self.x_max = 1.
        # form components
        self.Qmanual_edit = QtGui.QCheckBox(self.base_widget)
        self.Qnum_front = QtGui.QSpinBox(self.base_widget)
        self.Qnum_back = QtGui.QSpinBox(self.base_widget)
        self.Qnum_dist = QtGui.QSpinBox(self.base_widget)
        self.Qnum_cells = QtGui.QSpinBox(self.base_widget)
        self.Qcheck1 = QtGui.QCheckBox(self.base_widget)
        self.Qset_const = QtGui.QPushButton(self.base_widget)

        self.Qset_const.setText("Push")
        # create gui

        self.setup_widget()
        self.add_pivy()

    def setup_widget(self):
        self.Qnum_cells.setValue(20)
        self.Qnum_front.setValue(len(self.glider_2d.front.controlpoints))
        self.Qnum_back.setValue(len(self.glider_2d.back.controlpoints))
        self.Qnum_dist.setValue(len(self.glider_2d.cell_dist_controlpoints))
        self.base_widget.connect(self.Qmanual_edit, QtCore.SIGNAL('stateChanged(int)'), self.line_edit)
        self.base_widget.connect(self.Qcheck1, QtCore.SIGNAL('stateChanged(int)'), self.rib_edit)
        self.base_widget.connect(self.Qnum_cells, QtCore.SIGNAL('valueChanged(int)'), self.update_shape)
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
        self.front_cpc.control_points[-1].constraint = lambda pos: [pos[0], 0., 0.]
        self.update_shape()

    def update_num_back(self, val):
        self.glider_2d.back.numpoints = val
        self.back_cpc.set_control_points(vector3D(self.glider_2d.back.controlpoints))
        self.update_shape()

    def add_pivy(self):
        # SHAPE
        self.front_cpc = ControlPointContainer(vector3D(self.glider_2d.front.controlpoints))
        self.back_cpc = ControlPointContainer(vector3D(self.glider_2d.back.controlpoints))
        self.front_cpc.on_drag.append(self.update_data_back)
        self.back_cpc.on_drag.append(self.update_data_front)
        # self.front_cpc.control_points[-1].constraint = lambda pos: [pos[0], 0., 0.]
        #
        self.shape = coin.SoSeparator()
        #
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.front_cpc)
        self.task_separator.addChild(self.back_cpc)

        self.task_separator.addChild(Line(self.obj.glider_instance.shape_simple[0]).object)
        self.task_separator.addChild(Line(self.obj.glider_instance.shape_simple[1]).object)
        
        # CELL-POS
        self.rib_pos_cpc = ControlPointContainer(vector3D(self.glider_2d.cell_dist_controlpoints))
        self.task_separator.addChild(self.rib_pos_cpc)
        self.rib_pos_cpc.on_drag.append(self.update_shape)

        self.update_shape()

    def update_data_back(self):
        self.back_cpc.control_points[-1].set_x(self.front_cpc.control_points[-1].x)
        self.update_shape()

    def update_data_front(self):
        self.front_cpc.control_points[-1].set_x(self.back_cpc.control_points[-1].x)
        self.update_shape()

    def update_const(self):
        const_dist = self.glider_2d.depth_integrated()
        self.task_separator.addChild(Line(const_dist).object)
        self.glider_2d.cell_dist.controlpoints = fitbezier(const_dist, self.glider_2d.cell_dist._bezierbase)
        self.rib_pos_cpc.set_control_points(self.glider_2d.cell_dist_controlpoints)
        self.update_shape()

    def update_shape(self, arg=None):
        print("absdlfks")
        self.glider_2d.front.controlpoints = [i[:-1] for i in self.front_cpc.control_point_list]
        self.glider_2d.back.controlpoints = [i[:-1] for i in self.back_cpc.control_point_list]
        self.glider_2d.cell_dist_controlpoints = [i[:-1] for i in self.rib_pos_cpc.control_point_list]
        if arg is not None:
            self.glider_2d.cell_num = arg
        else:
            self.glider_2d.cell_num = self.Qnum_cells.value()
        self.shape.removeAllChildren()
        ribs, front, back, dist_line = self.glider_2d.interactive_shape()
        self.shape.addChild(Line(front).object)
        self.shape.addChild(Line(back).object)
        for rib in ribs:
            self.shape.addChild(Line(rib).object)
        self.shape.addChild(Line(dist_line).object)
        for i in dist_line:
            self.shape.addChild(Line([[0, i[1]], i, [i[0], 0]], color="gray").object)



class airfoil_tool(base_tool):
    def __init__(self, obj):
        super(airfoil_tool, self).__init__(obj, widget_name="airfoil tool")
        self.shape = coin.SoSeparator()
        self.task_separator.addChild(self.shape)
        self.glider_2d = Glider_2D.import_from_glider(self.obj.glider_instance)
        self.draw_shape()

    def draw_shape(self):
        self.shape.removeAllChildren()
        ribs, front, back, dist_line = self.glider_2d.interactive_shape()
        self.shape.addChild(Line(front).object)
        self.shape.addChild(Line(back).object)
        for rib in ribs:
            self.shape.addChild(Line(rib).object)

    def merge_diagram(self):
        """
            -create controlpoints
            -draw line
            -make function for airfoil positions
        """
        pass

