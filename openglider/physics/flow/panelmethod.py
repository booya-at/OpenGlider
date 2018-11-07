import paraBEM                            # python panel method package
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
        v_inf = None
        vtk_flow_output = "."

    def __init__(self, glider, config=None):
        self.config = self.DefaultConf(config)
        self.glider = glider
        if not self.config.symmetric_case:
            self.glider = glider.copy_complete()
        self.case = None
        self.mesh = None
        self.result = False

    def _get_case(self):

        mesh = self.get_mesh()

        vertices, panels, boundary = mesh.get_indexed()

        bem_vertices = [paraBEM.PanelVector3(*v) for v in vertices]
        self.vertices = bem_vertices

        self.bem_panels = [paraBEM.Panel3([bem_vertices[i] for i in panel]) for panel in panels["hull"]]
        self.bem_trailing_edge = [bem_vertices[i] for i in boundary["trailing_edge"]]


        if self.config.symmetric_case:
            for panel in self.bem_panels:
                if abs(panel.center.y) > 0.00000001:
                    panel.set_symmetric()

        case = self.config.solver(self.bem_panels, self.bem_trailing_edge)
        v_inf = getattr(self.config, "v_inf", None)
        if v_inf is None:
            v_inf = self.glider.lineset.v_inf
        case.v_inf = paraBEM.Vector3(*v_inf)
        case.create_wake(length=self.config.wake_length, count=self.config.wake_panels)
        case.mom_ref_point = paraBEM.Vector3(1.25, 0, -5)  # todo
        case.A_ref = self.glider.area
        case.farfield = self.config.far_field_coeff

        return case

    def run(self):
        if self.case is None:
            self.case = self._get_case()
        temp = self.case.run()
        self.result = True
        return temp

    @property
    def pressure(self):
        """return a pressure map (polygon -> pressure)"""
        assert self.case is not None
        rho = self.config.rho_air
        for i, pan in enumerate(self.bem_panels):
            cp = pan.cp
            if cp < -4:
                cp = -4
            if cp > 1:
                cp = 1
            yield -(cp - 1) * rho * self.case.v_inf.norm()**2 / 2

    def export_vtk(self, dir=None):
        assert self.case is not None
        dir = dir or self.config.vtk_flow_output
        writer = CaseToVTK(self.case, dir)
        writer.write_panels()
        writer.write_wake_panels()

    @property
    def ca(self):
        return 0



