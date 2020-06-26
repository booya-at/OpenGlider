from __future__ import division

from copy import deepcopy

import matplotlib.pyplot as plt
import numpy as np

import FreeCADGui as Gui
from openglider.glider.in_out.export_3d import parabem_Panels
from openglider.utils.distribution import Distribution
from PySide import QtCore, QtGui

from .tools import BaseTool, input_field, text_field
from pivy.graphics import (COLORS, InteractionSeparator, Line, Marker,
                                  coin)


class Polars(BaseTool):
    widget_name = 'Aerdynamic computations'
    hide = False
    try:
        parabem = __import__('parabem')
        pan3d = __import__('parabem.pan3d', globals(), locals(), ['abc'])
        parabem_utils = __import__('parabem.utils', globals(), locals(), ['abc'])
    except ImportError:
        parabem = None

    def __init__(self, obj):
        super(Polars, self).__init__(obj)
        self.setup_widget()

    def setup_widget(self):
        self.Qweight = QtGui.QDoubleSpinBox()
        self.Qpilot_drag = QtGui.QDoubleSpinBox()
        self.Qparasit_wing_drag_c0 = QtGui.QDoubleSpinBox()
        self.Qparasit_wing_drag_c2 = QtGui.QDoubleSpinBox()
        self.Qmom_z_ref_point = QtGui.QDoubleSpinBox()
        self.Qcompute = QtGui.QPushButton("create plots")

        self.layout.setWidget(0, text_field, QtGui.QLabel('total weight [kg]'))
        self.layout.setWidget(0, input_field, self.Qweight)
        self.layout.setWidget(1, text_field, QtGui.QLabel('pilot drag (cw_p * A_p) normalized'))
        self.layout.setWidget(1, input_field, self.Qpilot_drag)
        self.layout.setWidget(2, text_field, QtGui.QLabel('wing drag c0'))
        self.layout.setWidget(2, input_field, self.Qparasit_wing_drag_c0)
        self.layout.setWidget(3, text_field, QtGui.QLabel('wing drag c2'))
        self.layout.setWidget(3, input_field, self.Qparasit_wing_drag_c2)
        self.layout.setWidget(4, text_field, QtGui.QLabel('z position of moment_ref_point'))
        self.layout.setWidget(4, input_field, self.Qmom_z_ref_point)
        self.layout.setWidget(5, text_field, self.Qcompute)

        self.Qweight.setMinimum(10)
        self.Qweight.setMaximum(300)
        self.Qweight.setValue(90)

        self.Qpilot_drag.setMinimum(0)
        self.Qpilot_drag.setMaximum(0.1)
        self.Qpilot_drag.setValue(0.01)

        self.Qparasit_wing_drag_c0.setMinimum(0)
        self.Qparasit_wing_drag_c0.setMaximum(0.1)
        self.Qparasit_wing_drag_c0.setValue(0.01)

        self.Qparasit_wing_drag_c2.setMinimum(0)
        self.Qparasit_wing_drag_c2.setMaximum(0.1)
        self.Qparasit_wing_drag_c2.setValue(0.03)

        self.Qmom_z_ref_point.setMinimum(-100)
        self.Qmom_z_ref_point.setMaximum(100)
        self.Qmom_z_ref_point.setValue(-7)

        self.Qcompute.clicked.connect(self.compute)
        self.create_potential_table()

    def compute(self):
        self.solve_const_vert_Force()
    
    def create_potential_table(self):
        if not self.parabem:
            self.QWarning = QtGui.QLabel('no panel_method installed')
            self.layout.addWidget(self.QWarning)
        else:
            self._vertices, self._panels, self._trailing_edges = parabem_Panels(
                self.parametric_glider.get_glider_3d(),
                midribs=0,
                profile_numpoints=50,
                num_average=7,
                distribution=Distribution.from_nose_cos_distribution(0.2),
                symmetric=True
                )
            case = self.pan3d.DirichletDoublet0Source0Case3(self._panels, self._trailing_edges)
            case.A_ref = self.parametric_glider.shape.area
            # att point
            case.mom_ref_point = self.parabem.Vector3(1.25, 0, self.Qmom_z_ref_point.value())
            case.v_inf = self.parabem.Vector(self.parametric_glider.v_inf)
            case.drag_calc = 'trefftz'
            case.farfield = 5
            case.create_wake(10000000, 20)
            pols = case.polars(self.parabem_utils.v_inf_deg_range3(case.v_inf, 2, 30, 30))
            self.cL = []
            self.cDi = []
            self.cPi = []
            self.alpha = []
            for i in pols.values:
                self.alpha.append(i.alpha)
                self.cL.append(i.cL)
                self.cDi.append(i.cD)
                self.cPi.append(i.cP)
            self.alpha = np.array(self.alpha)
            self.cL = np.array(self.cL)
            self.cDi = np.array(self.cDi)
            self.cPi = np.array(self.cPi)

    def solve_const_vert_Force(self):
        from scipy.optimize import newton_krylov
        # constants:
        c0 = self.Qparasit_wing_drag_c0.value()      # const profile drag
        c2 = self.Qparasit_wing_drag_c2.value()      # c2 * cl**2 + c0 = cDpr
        cDpi = self.Qpilot_drag.value()              # drag cooefficient of pilot
        mass = self.Qweight.value()

        rho = 1.2
        g = 9.81
    
        area = self.parametric_glider.shape.area
        cDl = self.obj.Proxy.getGliderInstance().lineset.get_normalized_drag() / area * 2
        alpha = self.alpha
        cL = self.cL
        cDi = self.cDi

        cD_ges = (cDi + np.ones_like(cDi) * (cDpi + cDl + c0) + c2 * cL**2)

        def minimize(phi):
            return np.arctan(cD_ges / cL) - self.alpha + phi

        def gz():
            return cL / cD_ges

        def vel(phi):
            return np.sqrt(2 * mass * g * np.cos(alpha - phi) / cL / rho / area)

        def find_zeros(x, y):
            sign = np.sign(y[0])
            i = 1
            while i < len(y):
                if sign != np.sign(y[i]):
                    return x[i-1] + (x[i-1] - x[i]) * y[i-1] / (y[i] - y[i-1])
                i += 1
                if i > len(x):
                    return


        phi = newton_krylov(minimize, np.ones_like(self.alpha)) 
        a_p = [find_zeros(vel(phi), phi), find_zeros(gz(), phi)]
        plt.plot(vel(phi), gz())
        plt.plot(vel(phi), phi)
        plt.plot(a_p[0], a_p[1], marker='o')
        plt.plot()
        plt.grid()
        plt.show()

    def accept(self):
        Gui.Control.closeDialog()

    def reject(self):
        Gui.Control.closeDialog()




class PanelTool(BaseTool):
    widget_name = 'Properties'
    hide = True
    try:
        parabem = __import__('parabem')
        pan3d = __import__('parabem.pan3d', globals(), locals(), ['abc'])
    except ImportError:
        parabem = None

    def __init__(self, obj):
        super(PanelTool, self).__init__(obj)
        if not self.parabem:
            self.QWarning = QtGui.QLabel('no panel_method installed')
            self.layout.addWidget(self.QWarning)
        else:
            self.case = None
            self.Qrun = QtGui.QPushButton('run')
            self.Qmidribs = QtGui.QSpinBox()
            self.Qsymmetric = QtGui.QCheckBox()
            self.Qmean_profile = QtGui.QCheckBox()
            self.Qprofile_points = QtGui.QSpinBox()
            self.Qstream_points = QtGui.QSpinBox()
            self.Qstream_radius = QtGui.QDoubleSpinBox()
            self.Qstream_interval = QtGui.QDoubleSpinBox()
            self.Qstream_num = QtGui.QSpinBox()
            self.Qmax_val = QtGui.QDoubleSpinBox()
            self.Qmin_val = QtGui.QDoubleSpinBox()
            self.cpc = InteractionSeparator(self.rm)
            self.stream = coin.SoSeparator()
            self.glider_result = coin.SoSeparator()
            self.marker = Marker([[0, 0, 0]], dynamic=True)
            self.setup_widget()
            self.setup_pivy()

    def setup_widget(self):
        self.layout.setWidget(0, text_field, QtGui.QLabel('profile points'))
        self.layout.setWidget(0, input_field, self.Qprofile_points)
        self.layout.setWidget(1, text_field, QtGui.QLabel('midribs'))
        self.layout.setWidget(1, input_field, self.Qmidribs)
        self.layout.setWidget(2, text_field, QtGui.QLabel('symmetric'))
        self.layout.setWidget(2, input_field, self.Qsymmetric)
        self.layout.setWidget(3, text_field, QtGui.QLabel('mean profile'))
        self.layout.setWidget(3, input_field, self.Qmean_profile)
        self.layout.setWidget(4, text_field, QtGui.QLabel('number of streams'))
        self.layout.setWidget(4, input_field, self.Qstream_points)
        self.layout.setWidget(5, text_field, QtGui.QLabel('stream radius'))
        self.layout.setWidget(5, input_field, self.Qstream_radius)
        self.layout.setWidget(6, text_field, QtGui.QLabel('points per streamline'))
        self.layout.setWidget(6, input_field, self.Qstream_num)
        self.layout.setWidget(7, text_field, QtGui.QLabel('stream interval'))
        self.layout.setWidget(7, input_field, self.Qstream_interval)
        self.layout.setWidget(8, text_field, QtGui.QLabel('min_val'))
        self.layout.setWidget(8, input_field, self.Qmin_val)
        self.layout.setWidget(9, text_field, QtGui.QLabel('max_val'))
        self.layout.setWidget(9, input_field, self.Qmax_val)
        self.layout.addWidget(self.Qrun)

        self.Qmidribs.setMaximum(5)
        self.Qmidribs.setMinimum(0)
        self.Qmidribs.setValue(0)
        self.Qprofile_points.setMaximum(50)
        self.Qprofile_points.setMinimum(10)
        self.Qprofile_points.setValue(20)
        self.Qsymmetric.setChecked(True)
        self.Qmean_profile.setChecked(True)
        self.Qstream_points.setMaximum(30)
        self.Qstream_points.setMinimum(1)
        self.Qstream_points.setValue(3)
        self.Qstream_radius.setMaximum(2)
        self.Qstream_radius.setMinimum(0)
        self.Qstream_radius.setValue(0.1)
        self.Qstream_radius.setSingleStep(0.1)
        self.Qstream_interval.setMaximum(1.000)
        self.Qstream_interval.setMinimum(0.00001)
        self.Qstream_interval.setValue(0.02)
        self.Qstream_interval.setSingleStep(0.01)

        self.Qstream_num.setMaximum(300)
        self.Qstream_num.setMinimum(5)
        self.Qstream_num.setValue(70)

        self.Qmin_val.setMaximum(3)
        self.Qmin_val.setMinimum(-10)
        self.Qmin_val.setValue(-3)
        self.Qmin_val.setSingleStep(0.001)

        self.Qmax_val.setMaximum(10)
        self.Qmax_val.setMinimum(0)
        self.Qmax_val.setValue(1)
        self.Qmax_val.setSingleStep(0.01)


        self.Qstream_points.valueChanged.connect(self.update_stream)
        self.Qstream_radius.valueChanged.connect(self.update_stream)
        self.Qstream_interval.valueChanged.connect(self.update_stream)
        self.Qstream_num.valueChanged.connect(self.update_stream)

        self.Qmin_val.valueChanged.connect(self.show_glider)
        self.Qmax_val.valueChanged.connect(self.show_glider)

        self.Qrun.clicked.connect(self.run)

    def setup_pivy(self):
        self.cpc.register()
        self.task_separator.addChild(self.cpc)
        self.task_separator.addChild(self.stream)
        self.task_separator.addChild(self.glider_result)
        self.cpc += [self.marker]
        self.marker.on_drag_release.append(self.update_stream)
        self.marker.on_drag.append(self.update_stream_fast)

    def update_stream(self):
        self.stream.removeAllChildren()
        if self.case:
            point = list(self.marker.points[0].getValue())
            points = np.random.random((self.Qstream_points.value(), 3)) - np.array([0.5, 0.5, 0.5])
            points *= self.Qstream_radius.value()
            points += np.array(point)
            points = points.tolist()
            for p in points:
                pts = self.stream_line(p, self.Qstream_interval.value(), self.Qstream_num.value())
                self.stream.addChild(Line(pts, dynamic=False))

    def update_stream_fast(self):
        self.stream.removeAllChildren()
        if self.case:
            point = list(self.marker.points[0].getValue())
            pts = self.stream_line(point, 0.05, 10)
            self.stream.addChild(Line(pts, dynamic=False))

    def update_glider(self):
        self.obj.ViewObject.num_ribs = self.Qmidribs.value()
        self.obj.ViewObject.profile_num = self.Qprofile_points.value()

    def stream_line(self, point, interval, numpoints):
        flow_path = self.case.flow_path(self.parabem.Vector3(*point), interval, numpoints)
        return [[p.x, p.y, p.z] for p in flow_path]

    def create_panels(self, midribs=0, profile_numpoints=10, mean=False, symmetric=True):
        self._vertices, self._panels, self._trailing_edges = parabem_Panels(
            self.parametric_glider.get_glider_3d(),
            midribs=midribs,
            profile_numpoints=profile_numpoints,
            num_average=mean*5,
            distribution=Distribution.from_nose_cos_distribution(0.2),
            symmetric=symmetric)

    def run(self):
        self.update_glider()
        self.create_panels(self.Qmidribs.value(), self.Qprofile_points.value(),
                           self.Qmean_profile.isChecked(), self.Qsymmetric.isChecked())
        del self.case
        self.case = self.pan3d.DirichletDoublet0Source0Case3(self._panels, self._trailing_edges)
        self.case.v_inf = self.parabem.Vector(self.parametric_glider.v_inf)
        self.case.farfield = 5
        self.case.create_wake(9999, 10)
        self.case.run()
        self.show_glider()

    def show_glider(self):
        self.glider_result.removeAllChildren()
        verts = [list(i) for i in self.case.vertices]
        cols = [i.cp for i in self.case.vertices]
        pols = []
        pols_i =[]
        count = 0
        count_krit = (self.Qmidribs.value() + 1) * (self.Qprofile_points.value() - self.Qprofile_points.value() % 2)
        for pan in self._panels[::-1]:
            count += 1
            for vert in pan.points:
                #verts.append(list(vert))
                pols_i.append(vert.nr)
            pols_i.append(-1)     # end of pol
            if count % count_krit == 0:
                pols.append(pols_i)
                pols_i = []
        if pols_i:
            pols.append(pols_i)
        vertex_property = coin.SoVertexProperty()

        for i, col in enumerate(cols):
            vertex_property.orderedRGBA.set1Value(i, coin.SbColor(self.color(col)).getPackedValue())
            
        vertex_property.vertex.setValues(0, len(verts), verts)
        vertex_property.materialBinding = coin.SoMaterialBinding.PER_VERTEX_INDEXED

        vertex_property.normalBinding = coin.SoNormalBinding.PER_FACE

        shape_hint = coin.SoShapeHints()
        shape_hint.vertexOrdering = coin.SoShapeHints.COUNTERCLOCKWISE
        shape_hint.creaseAngle = np.pi / 2
        self.glider_result.addChild(shape_hint)
        self.glider_result.addChild(vertex_property)
        for panels in pols:
            face_set = coin.SoIndexedFaceSet()
            face_set.coordIndex.setValues(0, len(panels), panels)
            self.glider_result.addChild(face_set)


        p1 = np.array(self.case.center_of_pressure)
        f = np.array(self.case.force)
        line = Line([p1, p1 + f])
        self.glider_result.addChild(line)

    def color(self, value):
        def f(n, i, x):
            if ((i - 1) / n) < x < (i / n):
                return (n * x + 1 - i)
            elif (i / n) <= x < ((i + 1) / n):
                return  (- n * x + 1 + i)
            else:
                return 0
        max_val=self.Qmax_val.value()
        min_val=self.Qmin_val.value()
        red = np.array(COLORS['red'])
        blue = np.array(COLORS['blue'])
        yellow = np.array(COLORS['yellow'])
        white = np.array(COLORS['white'])
        norm_val = (value - min_val) / (max_val - min_val)
        return list(f(3, 0, norm_val) * red + f(3,1,norm_val) * yellow + f(3,2,norm_val) * white + f(3,3,norm_val) * blue)


def create_fem_dict(par_glider):
    # not yet working
    
    # create a parabem object and compute the pressure

    # create a dict with:
    #   nodes, elements, forces, bc, joints
    vertices, panels, trailing_edges = parabem_Panels(
        par_glider.get_glider_3d(),
        midribs=0,
        profile_numpoints=50,
        num_average=4,
        distribution=Distribution.from_nose_cos_distribution(0.2),
        symmetric=True
        )

    # case.A_ref = par_glider.flat_area
    # case.v_inf = parabem.Vector(glider.v_inf)
    # self.case.farfield = 5
    # self.case.create_wake(9999, 10)
    # self.case.run()


class VelCalculator(QtGui.QDialog):
    pass
