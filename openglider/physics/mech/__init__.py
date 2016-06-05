from openglider.utils import Config
from openglider.physics.base import GliderCase
from openglider.physics.flow import GliderPanelMethod
from openglider.mesh import Mesh, Vertex

import paraFEM
from paraEigen import vector3


class GliderFemCase(GliderCase):
    class DefaultConf(GliderCase.DefaultConf):
        fem_timestep = 0.0001
        fem_steps = 10
        fem_output = 100
        pass

    def __init__(self, glider, config=None, flow_case=None):
        super(GliderFemCase, self).__init__(glider, config)
        self.glider = glider.copy_complete()
        self.flow_case = flow_case or GliderPanelMethod(self.glider, config)
        self.mesh = self.get_mesh()
        self.config = self.DefaultConf(config)
        self.case = None

    def run(self):
        if not self.flow_case.result:
            self.flow_case.run()
        self.fix_attachment_points()
        pressure = list(self.flow_case.pressure)
        vertices, polygons, boundary = self.mesh.get_indexed()
        rib_material = paraFEM.MembraneMaterial(1000, 0.3)
        hull_material = paraFEM.MembraneMaterial(1000, 0.3)
        nodes = [paraFEM.Node(*vertex) for vertex in vertices]
        for fixed_index in polygons["attachment_points"][0]:
            nodes[fixed_index].fixed = vector3(0, 0, 0)
        elements = []
        for i, polygon in enumerate(polygons["hull"]):
            poly_nodes = [nodes[index] for index in polygon]

        # TODO: use a basic membrane constructor (paraFEM)
            if len(poly_nodes) == 3:
                element = paraFEM.Membrane3(poly_nodes, hull_material)
                element.setConstPressure(pressure[i])
                elements.append(element)
            elif len(poly_nodes) == 4:
                element = paraFEM.Membrane4(poly_nodes, hull_material)
                element.setConstPressure(pressure[i])
                elements.append(element)

        for i, polygon in enumerate(polygons["ribs"]):
            poly_nodes = [nodes[index] for index in polygon]
            if len(poly_nodes) == 3:
                element = paraFEM.Membrane3(poly_nodes, rib_material)
                elements.append(element)
            elif len(poly_nodes) == 4:
                element = paraFEM.Membrane4(poly_nodes, rib_material)
                elements.append(element)
        self.case = paraFEM.Case(elements)
        self.writer = paraFEM.vtkWriter("/tmp/Fem/output")

        self.writer.writeCase(self.case, 0)
        for i in range(self.config.fem_steps):
            self.case.makeStep(self.config.fem_timestep)
            self.writer.writeCase(self.case, 0)

    def fix_attachment_points(self):
        attachment_points = [Vertex(*v.get_position()) for v in self.glider.lineset.attachment_points]
        self.mesh += Mesh({"attachment_points": [attachment_points]}, {"ribs": attachment_points})
        self.mesh.delete_duplicates()
