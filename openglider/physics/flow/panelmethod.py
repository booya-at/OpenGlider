import paraBEM                            # python panel methode package
from paraBEM.vtk_export import CaseToVTK  # export to vtk file format
import paraBEM.pan3d as pan3d

from openglider.physics.base import GliderCase


class GliderPanelMethod(GliderCase):
    class DefaultConf(GliderCase.DefaultConf):
        solver = pan3d.DirichletDoublet0Source0Case3
        wake_length = 1000
        wake_panels = 10
        far_field_coeff = 5
        rho_air = 1.2

    def __init__(self, glider, config=None):
        self.glider = glider.copy_complete()
        self.config = self.DefaultConf(config)
        self.case = None
        self.mesh = None

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
        case.create_wake(length=self.config.wake_length, count=self.config.wake_panels)
        case.mom_ref_point = paraBEM.Vector3(1.25, 0, -5)  # todo!
        case.A_ref = self.glider.area
        case.farfield = self.config.far_field_coeff

        return case

    def run(self):
        if self.case is None:
            self.case = self._get_case()
        temp = self.case.run()
        self.apply_pressure()
        self.result = True
        return temp

    def apply_pressure(self):
        """return a pressure map (polygon -> pressure)"""
        assert self.case is not None
        cell_mesh = self.mesh.polygons["hull"]
        rho = self.config.rho_air
        for i, pan in enumerate(self.bem_panels):
            cell_mesh[i].pressure = pan.cp * rho * self.case.v_inf.norm()**2 / 2

    def export_vtk(self, path):
        assert self.case is not None
        writer = CaseToVTK(self.case, path)
        writer.write_panels()
        writer.write_wake_panels()



