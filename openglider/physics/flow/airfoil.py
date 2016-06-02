import paraBEM                            # python panel methode package
from paraBEM.vtk_export import CaseToVTK  # export to vtk file format
#from paraBEM.utils import check_path      # check path and create directory
import paraBEM.pan2d as pan2d             # 2d panel-methods and solution-elements

from openglider.utils import Config
from openglider.physics.base import GliderCase


class AirfoilPanelMethod(object):
    class DefaultConf(Config):
        solver = pan2d.DirichletDoublet0Source0Case2
        wake_length = 1000
        wake_panels = 10
        far_field_coeff = 5

    def __init__(self, airfoil, config=None):
        self.airfoil = airfoil
        self.config = self.DefaultConf(config)
        self.case = None

    def _get_case(self):
        mesh = self.get_mesh()

        vertices, panels, boundary = mesh.get_indexed()

        bem_vertices = [paraBEM.PanelVector3(*v) for v in vertices]
        self.vertices = bem_vertices

        self.bem_panels = [paraBEM.Panel3([bem_vertices[i] for i in panel]) for panel in panels["hull"]]
        self.bem_trailing_edge = [bem_vertices[i] for i in boundary["trailing_edge"]]

        case = self.config.solver(self.bem_panels, self.bem_trailing_edge)
        if not hasattr(self.config, "v_inf"):
            self.config.v_inf = self.glider.ribs[0].v_inf
        case.v_inf = paraBEM.Vector3(*self.config.v_inf)
        #case.create_wake(length=self.config.wake_length, count=self.config.wake_panels)
        case.mom_ref_point = paraBEM.Vector3(1.25, 0, -5)  # todo!
        case.A_ref = self.glider.area
        case.farfield = self.config.far_field_coeff

        return case

    def run(self):
        if self.case is None:
            self.case = self._get_case()
        return self.case.run()

    def export_vtk(self, path):
        assert self.case is not None
        writer = CaseToVTK(self.case, path)
        writer.write_panels()
        writer.write_wake_panels()



