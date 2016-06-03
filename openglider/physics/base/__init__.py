from openglider.utils import Config
from openglider.utils.distribution import Distribution
from openglider.mesh import Mesh


class GliderCase(object):
    """simplification of the simulation tools."""
    class DefaultConf(Config):
        cell_numpoints = 2
        distribution = Distribution.from_nose_cos_distribution(50, 0.2)

    def __init__(self, glider, config=None):
        self.glider = glider
        self.config = self.DefaultConf(config)
        self.mesh = None

    def __json__(self):
        return {
            "glider": self.glider,
            "config": self.config,
        }

    def get_mesh(self):
        if self.mesh is None:
            dist = self.config.distribution.copy()
            dist.add_glider_fixed_nodes(self.glider)

            self.glider.profile_x_values = dist
            m = Mesh(name="glider_mesh")
            for cell in self.glider.cells:
                m += cell.get_mesh(self.config.cell_numpoints)
            for rib in self.glider.ribs:
                m += Mesh.from_rib(rib)
            m.delete_duplicates()
            self.mesh = m
        return self.mesh
