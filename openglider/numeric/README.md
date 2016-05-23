# [numeric](../README.md)

the numeric-module provides functionlity for simulating a glider.

## submodules

 - [mesh](./mesh/README.md)  
 - [flow](./flow/README.md)
 - [mech](./mech/README.md)

## future:
the simulation is splitted into 3 parts: mesh, flow and mech
a base class provides easy access to all these methodes.

possebility for different solver by subclassing the case class:
    reimplement: setup(config), run()
the config is a simple class which get monkey patched.

To iterate flow and structural analysis simple iterating the case should be possible. The case itself should not have any simplification to do this.


## api-design
```python

from openglider.numeric import GliderCase
...
# create case from glider
case = gliderCase(glider)

# prepare the mesh ()

config = case.mesh.defaultConfig
config.numpoints = 100 # ...

case.mesh.setup(config) # by default the default config is used
case.mesh.run()

# prepare the flow simulation
config = case.flow.config
config.visible_output = True

case.flow.setup(config)
case.flow.run()

# prepare the FEM smulation
config = case.mech.config
config.timestep = 0.0001
config.num_vis_export = 100

case.mech.setup(config)
case.mech.run()

```
