from openglider.utils import Config
from openglider.utils.distribution import Distribution
from openglider.mesh import Mesh


class GliderCase():
    """simplification of the simulation tools."""
    def __init__(self, glider):
        self.glider = glider
        self.setupMesh()

    @property
    def conf(self):
        conf = {
            "cell_numpoints": 0,
            "dist": {
                "dist_type": "nose_cose",
                "arg": 0.2,
                "num_points": 30
            }
        }

        return Config(conf)

    def setupMesh(self):
        dist = Distribution.from_glider(self.glider, self.conf.dist.dist_type)
        self.glider.profile_x_values = dist(self.conf.dist.num_points)
        m = Mesh(name="glider_mesh")
        for cell in self.glider.cells:
            m += cell.get_mesh(self.conf.cell_numpoints)
        m.delete_duplicates()
        print(m.boundary_nodes["trailing_edge"])
