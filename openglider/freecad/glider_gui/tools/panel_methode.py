from PySide import QtGui
import numpy

from _tools import base_tool, input_field, text_field
from PPM.pan3d import DirichletDoublet0Source0Case3 as Case
import PPM
from pivy_primitives_new_new import Container, Marker, coin, Line


class panel_tool(base_tool):
    def __init__(self, obj):
        super(panel_tool, self).__init__(obj, widget_name="Properties", hide=False)
        self.case = None
        self.Qrun = QtGui.QPushButton("run")
        self.Qmidribs = QtGui.QSpinBox()
        self.Qprofile_points = QtGui.QSpinBox()
        self.Qstream_points = QtGui.QSpinBox()
        self.Qstream_radius = QtGui.QDoubleSpinBox()
        self.Qstream_interval = QtGui.QDoubleSpinBox()
        self.Qstream_num = QtGui.QSpinBox()
        self.cpc = Container()
        self.stream = coin.SoSeparator()
        self.marker = Marker([[0, 0, 0]], dynamic=True)
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        self.layout.setWidget(0, text_field, QtGui.QLabel("profile points"))
        self.layout.setWidget(0, input_field, self.Qprofile_points)
        self.layout.setWidget(1, text_field, QtGui.QLabel("midribs"))
        self.layout.setWidget(1, input_field, self.Qmidribs)
        self.layout.setWidget(2, text_field, QtGui.QLabel("number of streams"))
        self.layout.setWidget(2, input_field, self.Qstream_points)
        self.layout.setWidget(3, text_field, QtGui.QLabel("stream radius"))
        self.layout.setWidget(3, input_field, self.Qstream_radius)
        self.layout.setWidget(4, text_field, QtGui.QLabel("points per streamline"))
        self.layout.setWidget(4, input_field, self.Qstream_num)
        self.layout.setWidget(5, text_field, QtGui.QLabel("stream interval"))
        self.layout.setWidget(5, input_field, self.Qstream_interval)
        self.layout.addWidget(self.Qrun)

        self.Qmidribs.setMaximum(5)
        self.Qmidribs.setMinimum(0)
        self.Qmidribs.setValue(1)
        self.Qprofile_points.setMaximum(50)
        self.Qprofile_points.setMinimum(10)
        self.Qprofile_points.setValue(15)
        self.Qstream_points.setMaximum(30)
        self.Qstream_points.setMinimum(1)
        self.Qstream_points.setValue(5)
        self.Qstream_radius.setMaximum(2)
        self.Qstream_radius.setMinimum(0)
        self.Qstream_radius.setValue(0.3)
        self.Qstream_interval.setMaximum(1.000)
        self.Qstream_interval.setMinimum(0.00001)
        self.Qstream_interval.setValue(0.1)
        self.Qstream_interval.setSingleStep(0.01)
        self.Qstream_num.setMaximum(300)
        self.Qstream_num.setMinimum(5)
        self.Qstream_num.setValue(20)

        self.Qstream_points.valueChanged.connect(self.update_stream)
        self.Qstream_radius.valueChanged.connect(self.update_stream)
        self.Qstream_interval.valueChanged.connect(self.update_stream)
        self.Qstream_num.valueChanged.connect(self.update_stream)

        self.Qrun.clicked.connect(self.run)

    def setup_pivy(self):
        self.cpc.register(self.view)
        self.task_separator.addChild(self.cpc)
        self.task_separator.addChild(self.stream)
        self.cpc.addChild(self.marker)
        self.marker.on_drag_release.append(self.update_stream)

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

    def update_glider(self):
        self.obj.ViewObject.num_ribs = self.Qmidribs.value()
        self.obj.ViewObject.profile_num = self.Qprofile_points.value()

    def stream_line(self, point, interval, numpoints):
        flow_path = self.case.flow_path(PPM.Vector3(*point), interval, numpoints)
        return [[p.x, p.y, p.z] for p in flow_path.values]

    def create_panels(self, midribs=0, profile_numpoints=10):
        import PPM
        glider = self.obj.glider_instance.copy_complete()
        glider.profile_numpoints = profile_numpoints
        ribs = glider.return_ribs(midribs)

        # deleting the last vertex of every rib (no trailing edge gap)
        ribs = [rib[:-1] for rib in ribs]

        # get a numbered representation + flatten vertices
        i = 0
        vertices = [] 
        ribs_new = []
        for rib in ribs:
            rib_new = []
            for vertex in rib:
                rib_new.append(i)
                vertices.append(vertex)
                i += 1
            rib_new.append(rib_new[0])
            ribs_new.append(rib_new)
        ribs = ribs_new
        wake_edge = [rib[0] for rib in ribs]
        polygons = []
        for i, rib_i in enumerate(ribs[:-1]):
            rib_j = ribs[i+1]
            for k, _ in enumerate(rib_j[:-1]):
                l = k + 1
                p = [rib_i[k], rib_j[k], rib_j[l], rib_i[l]]
                polygons.append(p)

    # Panel3-methode
        self._vertices = [PPM.PanelVector3(*vertex) for vertex in vertices]
        self._panels = [PPM.Panel3([self._vertices[nr] for nr in pol]) for pol in polygons]
        _wake_edges = [self._vertices[i] for i in wake_edge]

        self.case.panels = self._panels
        self.case.wake_edges = _wake_edges

    def run(self):
        self.update_glider()
        self.case = Case()
        self.case.vinf = PPM.Vector3(10, 0, 3)
        self.create_panels(self.Qmidribs.value(), self.Qprofile_points.value())
        self.case.farfield = 5
        self.case.create_wake(20, 20)
        self.case.run()
