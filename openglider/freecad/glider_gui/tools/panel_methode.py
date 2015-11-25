from __future__ import division
import FreeCAD as App
import Plot
from FreeCAD import Base
from PySide import QtGui
import numpy

from openglider.glider.in_out.export_3d import ppm_Panels
from openglider.airfoil import Profile2D
from _tools import base_tool, input_field, text_field
from pivy_primitives_new_new import Container, Marker, coin, Line, COLORS


class polars(base_tool):
    try:
        ppm = __import__("ppm")
        pan3d = __import__("ppm.pan3d", globals(), locals(), ["abc"], -1)
        ppm_utils = __import__("ppm.utils", globals(), locals(), ["abc"], -1)
    except ImportError:
        ppm = None

    def __init__(self, obj):
        super(polars, self).__init__(obj, widget_name="Properties", hide=True)
        if not self.ppm:
            self.QWarning = QtGui.QLabel("no panel_methode installed")
            self.layout.addWidget(self.QWarning)
        else:
            self._vertices, self._panels, self._trailing_edges = ppm_Panels(
                self.glider_2d.get_glider_3d(),
                midribs=0,
                profile_numpoints=50,
                num_average=4,
                distribution=Profile2D.nose_cos_distribution(0.2),
                symmetric=True
                )
            progress_bar = Base.ProgressIndicator()
            progress_bar.start("running ppm", 0)
            case = self.pan3d.DirichletDoublet0Source0Case3(self._panels, self._trailing_edges)
            case.A_ref = self.glider_2d.flat_area
            case.mom_ref_point = self.ppm.Vector3(1.25, 0, -6)
            case.v_inf = self.ppm.Vector(self.glider_2d.v_inf)
            case.drag_calc = "trefftz"
            case.farfield = 5
            case.create_wake(10000000, 20)
            pols = case.polars(self.ppm_utils.vinf_deg_range3(case.v_inf, -10, 10, 30))
            cL = []
            cD = []
            cP = []
            alpha = []
            for i in pols.values:
                alpha.append(i.alpha)
                cL.append(i.cL)
                cD.append(i.cD * 10)
                cP.append(-i.cP)
            Plot.plot(cL, alpha, "Lift $c_L$")
            Plot.plot(cD, alpha, "Drag $c_D * 10$")
            Plot.plot(cP, alpha, "Pitch -$c_P$")
            Plot.ylabel("$\\alpha$")
            Plot.legend()
            Plot.grid()
            progress_bar.stop()



class panel_tool(base_tool):
    try:
        ppm = __import__("ppm")
        pan3d = __import__("ppm.pan3d", globals(), locals(), ["abc"], -1)
    except ImportError:
        ppm = None

    def __init__(self, obj):
        super(panel_tool, self).__init__(obj, widget_name="Properties", hide=True)
        if not self.ppm:
            self.QWarning = QtGui.QLabel("no panel_methode installed")
            self.layout.addWidget(self.QWarning)
        else:
            self.case = None
            self.Qrun = QtGui.QPushButton("run")
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
            self.cpc = Container()
            self.stream = coin.SoSeparator()
            self.glider_result = coin.SoSeparator()
            self.marker = Marker([[0, 0, 0]], dynamic=True)
            self.setup_widget()
            self.setup_pivy()

    def setup_widget(self):
        self.layout.setWidget(0, text_field, QtGui.QLabel("profile points"))
        self.layout.setWidget(0, input_field, self.Qprofile_points)
        self.layout.setWidget(1, text_field, QtGui.QLabel("midribs"))
        self.layout.setWidget(1, input_field, self.Qmidribs)
        self.layout.setWidget(2, text_field, QtGui.QLabel("symmetric"))
        self.layout.setWidget(2, input_field, self.Qsymmetric)
        self.layout.setWidget(3, text_field, QtGui.QLabel("mean profile"))
        self.layout.setWidget(3, input_field, self.Qmean_profile)
        self.layout.setWidget(4, text_field, QtGui.QLabel("number of streams"))
        self.layout.setWidget(4, input_field, self.Qstream_points)
        self.layout.setWidget(5, text_field, QtGui.QLabel("stream radius"))
        self.layout.setWidget(5, input_field, self.Qstream_radius)
        self.layout.setWidget(6, text_field, QtGui.QLabel("points per streamline"))
        self.layout.setWidget(6, input_field, self.Qstream_num)
        self.layout.setWidget(7, text_field, QtGui.QLabel("stream interval"))
        self.layout.setWidget(7, input_field, self.Qstream_interval)
        self.layout.setWidget(8, text_field, QtGui.QLabel("min_val"))
        self.layout.setWidget(8, input_field, self.Qmin_val)
        self.layout.setWidget(9, text_field, QtGui.QLabel("max_val"))
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
        self.Qmin_val.setSingleStep(0.01)

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
        self.cpc.register(self.view)
        self.task_separator.addChild(self.cpc)
        self.task_separator.addChild(self.stream)
        self.task_separator.addChild(self.glider_result)
        self.cpc.addChild(self.marker)
        self.marker.on_drag_release.append(self.update_stream)
        self.marker.on_drag.append(self.update_stream_fast)

    def update_stream(self):
        self.stream.removeAllChildren()
        if self.case:
            point = list(self.marker.points[0].getValue())
            points = numpy.random.random((self.Qstream_points.value(), 3)) - numpy.array([0.5, 0.5, 0.5])
            points *= self.Qstream_radius.value()
            points += numpy.array(point)
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
        flow_path = self.case.flow_path(self.ppm.Vector3(*point), interval, numpoints)
        return [[p.x, p.y, p.z] for p in flow_path.values]

    def create_panels(self, midribs=0, profile_numpoints=10, mean=False, symmetric=True):
        print(mean)
        self._vertices, self._panels, self._trailing_edges = ppm_Panels(
            self.glider_2d.get_glider_3d(),
            midribs=midribs,
            profile_numpoints=profile_numpoints,
            num_average=mean*5,
            distribution=Profile2D.nose_cos_distribution(0.2),
            symmetric=symmetric)

    def run(self):
        progress_bar = Base.ProgressIndicator()
        progress_bar.start("Progress bar test...", 10)
        self.update_glider()
        self.create_panels(self.Qmidribs.value(), self.Qprofile_points.value(),
                           self.Qmean_profile.isChecked(), self.Qsymmetric.isChecked())
        self.case = self.pan3d.DirichletDoublet0Source0Case3(self._panels, self._trailing_edges)
        self.case.v_inf = self.ppm.Vector(self.glider_2d.v_inf)
        self.case.farfield = 5
        self.case.create_wake(10000000, 20)
        self.case.run()
        self.show_glider()
        progress_bar.stop()

    def show_glider(self):
        self.glider_result.removeAllChildren()
        verts = [list(i) for i in self.case.vertices.values]
        cols = [i.cp for i in self.case.vertices.values]
        norms = [list(-1 * i.n) for i in self.case.panels]
        pols = []
        for pan in self._panels:
            for vert in pan.points:
                #verts.append(list(vert))
                pols.append(vert.nr)
            pols.append(-1)     # end of pol
        vertex_property = coin.SoVertexProperty()
        face_set = coin.SoIndexedFaceSet()

        for i, col in enumerate(cols):
            vertex_property.orderedRGBA.set1Value(i, coin.SbColor(self.color(col)).getPackedValue())
            
        vertex_property.vertex.setValues(0, len(verts), verts)
        vertex_property.materialBinding = coin.SoMaterialBinding.PER_VERTEX_INDEXED

        vertex_property.normal.setValues(0, len(norms), norms)
        vertex_property.normalBinding = coin.SoNormalBinding.PER_FACE

        face_set.coordIndex.setValues(0, len(pols), pols)

        self.glider_result.addChild(vertex_property)
        self.glider_result.addChild(face_set)

        p1 = numpy.array(self.case.center_of_pressure)
        print(p1)
        f = numpy.array(self.case.force)
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
        red = numpy.array(COLORS["red"])
        blue = numpy.array(COLORS["blue"])
        yellow = numpy.array(COLORS["yellow"])
        white = numpy.array(COLORS["white"])
        norm_val = (value - min_val) / (max_val - min_val)
        return list(f(3, 0, norm_val) * red + f(3,1,norm_val) * yellow + f(3,2,norm_val) * white + f(3,3,norm_val) * blue)