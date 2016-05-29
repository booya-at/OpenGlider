from openglider.utils import Config

class structuralSimulation(object):
    def __init__(self, baseSim, config=None):
        self.baseSim = baseSim  # not possible without a base sim
        self.config = config or self.defaultConfig


    def __json__(self):
        return{
                  "config": self.config,
              }

    @property
    def deafaultConfig(self):
        conf = Config()
        # materials

        # simulation config (timestep, steps,...)

        # visualization
    
        return conf
