import numpy as np

from openglider.utils import Config
from openglider.physics.base import GliderCase
from openglider.physics.flow import GliderPanelMethod
from openglider.mesh import Mesh, Vertex
from openglider.glider import ParametricGlider
from openglider.glider.parametric.lines import UpperNode2D

import paraFEM
from paraEigen import vector3


class GliderFemCase(GliderCase):
    class DefaultConf(GliderCase.DefaultConf):
        fem_timestep = 1.e-07
        fem_steps = 100
        fem_output = 100

        # material properties
        rib_elasticity = 3000
        rib_nue = 0.3
        rib_rho = 0.01

        hull_elasticity = 3000
        hull_nue = 0.3
        hull_rho = 0.01

        line_elasticity = 5000
        line_rho = 0.01

        d_velocity = 10
        pressure_ramp = 20000     # steps for linear pressure ramp
        caseType = "full"     #TODO rename to case_type
        line_numpoints = 2
        vtk_fem_output = "/tmp/Fem/output"
        insert_points = 5

    def __init__(self, glider, config=None, flow_case=None):
        super(GliderFemCase, self).__init__(glider, config)
        self.config = self.DefaultConf(config)
        if not self.config.symmetric_case:
            self.glider = glider.copy_complete()
        else:
            self.glider = glider
        self.flow_case = flow_case or GliderPanelMethod(glider, config)
        self.mesh = None
        self.case = None
        self.result = False

    def run(self):
        if not self.flow_case.result:
            self.flow_case.run()
            self.flow_case.export_vtk()

        mesh = self.get_mesh()
        pressure = list(self.flow_case.pressure)
        vertices, polygons, boundary = mesh.get_indexed()

        rib_material = paraFEM.MembraneMaterial(self.config.rib_elasticity,
                                                self.config.rib_nue)
        rib_material.d_velocity = self.config.d_velocity
        rib_material.d_structural = 0
        rib_material.rho = self.config.rib_rho

        hull_material = paraFEM.MembraneMaterial(self.config.hull_elasticity,
                                                 self.config.hull_nue)
        hull_material.d_velocity = self.config.d_velocity
        hull_material.d_structural = 0
        hull_material.rho = self.config.hull_rho

        truss_material = paraFEM.TrussMaterial(self.config.line_elasticity)
        truss_material.d_velocity = self.config.d_velocity
        truss_material.rho = self.config.line_rho

        self.nodes = [paraFEM.Node(*vertex) for vertex in vertices]

        if self.config.symmetric_case:
            for node in self.nodes:
                if node.position[1] < 0.000001:
                    if abs(node.position[1]) < 0.000001:
                        node.fixed = vector3(1, 0, 1)
                        if self.glider.has_center_cell:
                            pass # apply force constraint to get the influence of the other side on a rib
                    else:
                        pass # apply a symmetrical position constraint

        if self.config.caseType == "full":
            for index in boundary["lower_attachment_points"]:
                self.nodes[index].fixed = vector3(0, 0, 0)
        elif self.config.caseType == "line_forces":
            for index in boundary["lines"]:
                self.nodes[index].fixed = vector3(0, 0, 0)
        self.elements = []
        self.lines = []

        for i, polygon in enumerate(polygons["lines"]):
            poly_nodes = [self.nodes[index] for index in polygon]
            element = paraFEM.Truss(poly_nodes, truss_material)
            self.elements.append(element)
            self.lines.append(element)

        if self.config.caseType == "line_forces":
            line_map = self._get_line_map(self.lines)

        for i, polygon in enumerate(polygons["hull"]):
            poly_nodes = [self.nodes[index] for index in polygon]
            if len(set(poly_nodes)) < len(poly_nodes):
                # do not add self.elements with same index
                continue
            # TODO: use a basic membrane constructor (paraFEM)
            if len(poly_nodes) == 3:
                element = paraFEM.Membrane3(poly_nodes, hull_material)
                # element.setConstPressure(pressure[i])
                element.setConstPressure(0.)
                self.elements.append(element)
            elif len(poly_nodes) == 4:
                element = paraFEM.Membrane4(poly_nodes, hull_material, False)
                element.setConstPressure(pressure[i])
                element.setConstPressure(0.)
                self.elements.append(element)

        for i, polygon in enumerate(polygons["ribs"]): # + polygons["diagonals"]):
            poly_nodes = [self.nodes[index] for index in polygon]
            if len(set(poly_nodes)) < len(poly_nodes):
                # do not add self.elements with same index
                continue
            if len(poly_nodes) == 3:
                element = paraFEM.Membrane3(poly_nodes, rib_material)
                self.elements.append(element)
            elif len(poly_nodes) == 4:
                element = paraFEM.Membrane4(poly_nodes, rib_material, False)
                self.elements.append(element)


        self.case = paraFEM.Case(self.elements)
        cfl, bad_element = self.case.getExplicitMaxTimeStep()
        print("the cfl number is: {}".format(cfl))
        if cfl < self.config.fem_timestep:
            raise RuntimeError("the fem_timestep must be lower than the cfl number," + 
                               "make sure to set 'case.config.fem_timestep' to something lower than cfl " +
                               "cfl = {}, fem_timestep = {} \n".format(cfl, self.config.fem_timestep) + 
                               "element self.nodes are: {}".format(bad_element.self.nodes))
        self.writer = paraFEM.vtkWriter(self.config.vtk_fem_output)

        write_interval = self.config.fem_steps // self.config.fem_output or 1
        p_ramp = self.config.pressure_ramp
        self.writer.writeCase(self.case, 0.)
        for i in range(self.config.fem_steps):
            ramp = 1 - (i < p_ramp) * (1 - float(i) / p_ramp)
            self.case.explicitStep(self.config.fem_timestep, ramp)
            if (i % write_interval) == 0:
                print(int(i / write_interval))
                self.writer.writeCase(self.case, 0.)
        if self.config.caseType == "line_forces":
            for node, line in line_map.items():
                node.force = -np.array(line.getStress())

    def get_mesh(self):
        if self.mesh:
            return self.mesh
        else:
            self.glider = self.flow_case.glider
            self.mesh = self.flow_case.get_mesh()
        start = 0
        if (self.config.symmetric_case and self.glider.has_center_cell):
            start = 1
        for rib in self.glider.ribs[start:]:
            self.mesh += Mesh.from_rib(rib, mesh_option='QYqazip', filled=True)
        # for cell in self.glider.cells:  # TODO (not yet working)
        #     for diagonal in cell.diagonals:
        #         self.mesh += Mesh.from_diagonal(diagonal, cell, self.config.insert_points)
        if self.config.caseType == "line_forces":
            print("add uppermost lines to mesh")
            self.mesh += self.glider.lineset.get_upper_line_mesh(self.config.line_numpoints, breaks=False)

        if self.config.caseType == "full":
            print("add lines")
            self.mesh += self.glider.lineset.get_mesh(self.config.line_numpoints)

        self.mesh.delete_duplicates()
        return self.mesh

    def _get_line_map(self, fem_case_lines):
        line_map = {}
        for line in fem_case_lines:
            for node in line.nodes:
                pos = np.array(node.position)
                for attachment_point in self.glider.attachment_points:
                    if (attachment_point.vec - pos).dot(attachment_point.vec - pos) < 10e-8:
                        line_map[attachment_point] = line
        return line_map


    def set_line_forces(self, parametric_glider):
        assert(isinstance(parametric_glider, ParametricGlider))
        for node_2d in parametric_glider.lineset.self.nodes:
            if isinstance(node_2d, UpperNode2D):
                n3d_temp = node_2d.get_node(self.glider)
                for node in self.glider.attachment_points:
                    if (n3d_temp.rib == node.rib and
                       n3d_temp.rib_pos == node.rib_pos):
                        node_2d.force = np.array(node.force)
