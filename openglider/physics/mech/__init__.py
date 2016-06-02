from openglider.utils import Config
from openglider.physics.base import GliderCase
from openglider.physics.flow import GliderPanelMethod


class GliderFemCase(GliderCase):
    class DefaultConf(GliderCase.DefaultConf):
        # materials
        # simulation config (timestep, steps,...)
        # visualization
        pass

    def __init__(self, glider, config=None, flow_case=None):
        super(self, GliderFemCase).__init__(glider, config)
        self.flow_case = flow_case or GliderPanelMethod(glider, config)

    def run(self):
        if not self.flow_case.result:
            self.flow_case.run()
