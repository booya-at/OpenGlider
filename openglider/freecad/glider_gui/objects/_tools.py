from PySide import QtCore, QtGui
from pivy import coin
import FreeCADGui as Gui
from pivy_primitives import Line, vector3D, ControlPointContainer
from openglider.glider.glider import glider_2D

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
        super(shape_tool, self).__init__(obj, widget_name="shape-tool")
        self.glider_copy = self.obj.glider_instance.copy_complete()
        self.glider_2d = glider_2D.import_from_glider(self.obj.glider_instance)
        self.shape = None
        self.ribs = None
        self.cpc1 = None
        self.cpc2 = None
        self.line1 = None
        self.line2 = None
        self.x_max = 1.
        # form components
        self.manual_edit = QtGui.QCheckBox(self.base_widget)
        self.num_cells = QtGui.QSpinBox(self.base_widget)
        self.check1 = QtGui.QCheckBox(self.base_widget)
        self.set_const = QtGui.QPushButton(self.base_widget)
        self.set_const.setText("Push")
        # create gui

        self.setup_widget()
        self.add_pivy()

    def setup_widget(self):
        self.num_cells.setValue(20)
        self.base_widget.connect(self.manual_edit, QtCore.SIGNAL('stateChanged(int)'), self.line_edit)
        self.base_widget.connect(self.check1, QtCore.SIGNAL('stateChanged(int)'), self.rib_edit)
        self.base_widget.connect(self.num_cells, QtCore.SIGNAL('valueChanged(int)'), self.update_shape)
        self.base_widget.connect(self.set_const, QtCore.SIGNAL('clicked()'), self.update_const)

        self.layout.setWidget(1, text_field, QtGui.QLabel("num_cells"))
        self.layout.setWidget(1, input_field, self.num_cells)
        self.layout.setWidget(2, text_field, QtGui.QLabel("manual edit"))
        self.layout.setWidget(2, input_field, self.manual_edit)
        self.layout.setWidget(3, text_field, QtGui.QLabel("manual cell pos"))
        self.layout.setWidget(3, input_field, self.check1)
        self.layout.setWidget(4, text_field, QtGui.QLabel("constant AR"))
        self.layout.setWidget(4, input_field, self.set_const)

    def line_edit(self):
        self.cpc1.set_edit_mode(self.view)
        self.cpc2.set_edit_mode(self.view)

    def rib_edit(self):
        self.rib_pos_cpc.set_edit_mode(self.view)
        self.update_shape()

    def add_pivy(self):
        # SHAPE
        self.cpc1 = ControlPointContainer(vector3D(self.glider_2d.front))
        self.cpc2 = ControlPointContainer(vector3D(self.glider_2d.back))
        self.cpc1.on_drag.append(self.update_data_1)
        self.cpc2.on_drag.append(self.update_data_2)
        self.cpc1.control_points[-1].constraint = lambda pos: [pos[0], 0., 0.]
        #
        self.shape = coin.SoSeparator()
        #
        self.task_separator.addChild(self.shape)
        self.task_separator.addChild(self.cpc1)
        self.task_separator.addChild(self.cpc2)

        # CELL-POS
        self.rib_pos_cpc = ControlPointContainer([[0.33, 0.33, 0.], [0.66, 0.66, 0.]])
        self.task_separator.addChild(self.rib_pos_cpc)
        self.rib_pos_cpc.on_drag.append(self.update_shape)

        self.update_shape()

    def update_data_1(self):
        self.cpc2.control_points[0].set_x(self.cpc1.control_points[0].x)
        self.update_shape()

    def update_data_2(self):
        self.cpc1.control_points[0].set_x(self.cpc2.control_points[0].x)
        self.update_shape()

    def update_const(self):
        print("Hello")
        const_dist = self.glider_2d.depth_integrated()
        num = len(self.glider_2d._cell_dist._controlpoints)
        self.glider_2d._cell_dist.fit(const_dist, numpoints=num)
        self.rib_pos_cpc.set_control_points(self.glider_2d._cell_dist._controlpoints[1:-1])
        self.update_shape()

    def update_shape(self, arg=None):
        self.glider_2d.front = [i[:-1] for i in self.cpc1.control_point_list]
        self.glider_2d.back = [i[:-1] for i in self.cpc2.control_point_list]
        self.glider_2d.cell_distribution = [i[:-1] for i in self.rib_pos_cpc.control_point_list]
        if arg is not None:
            self.glider_2d.cell_num = arg
        else:
            self.glider_2d.cell_num = self.num_cells.value()
        self.shape.removeAllChildren()
        ribs, front, back, dist_line = self.glider_2d.shape()
        self.shape.addChild(Line(front).object)
        self.shape.addChild(Line(back).object)
        for rib in ribs:
            self.shape.addChild(Line(rib).object)
        if self.check1.checkState():
            self.shape.addChild(Line(dist_line).object)
            for i in dist_line:
                self.shape.addChild(Line([[0, i[1]], i, [i[0], 0]], color="gray").object)
