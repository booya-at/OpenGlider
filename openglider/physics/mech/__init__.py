from openglider.utils import Config
from openglider.physics.base import GliderCase
from openglider.physics.flow import GliderPanelMethod
from openglider.mesh import Mesh, Vertex

# import paraFEM

class GliderFemCase(GliderCase):
    class DefaultConf(GliderCase.DefaultConf):
        # materials
        # simulation config (timestep, steps,...)
        # visualization
        pass

    def __init__(self, glider, config=None, flow_case=None):
        super(GliderFemCase, self).__init__(glider, config)
        self.flow_case = flow_case or GliderPanelMethod(glider, config)
        self.mesh = self.get_mesh()

    def run(self):
        if not self.flow_case.result:
            self.flow_case.run()
        
    def fix_attachment_points(self):
        attachment_points = [Vertex(*v.get_position()) for v in self.glider.lineset.attachment_points]
        print(attachment_points3)
        self.mesh += Mesh({"attachment_points": attachment_points}, {})
        self.mesh.delete_duplicates()
        print(self.mesh.polygon["attachment_points"][0] in self.mesh.vertices)