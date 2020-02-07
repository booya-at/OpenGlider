# updaing projects to newer versions of openglider and dependencies
# defining an interface to do this?

import openglider
from freecad import app
from .glider import addProperty

# 1 write update function:
# 2 append function to "version_update"

def version_update(obj):
    from_0_01_to_0_02(obj)
    from_0_02_to_0_03(obj)

def from_0_01_to_0_02(obj):
    # no version was specified so we have to update to 0.2
    if not hasattr(obj, "openglider_version"):
        obj.addProperty('App::PropertyString',
                'openglider_version', 'metadata',
                'the version of openglider used to create this glider', 1)

        obj.addProperty('App::PropertyString',
                'freecad_version', 'metadata',
                'the version of openglider used to create this glider', 1)

        obj.openglider_version = "0.02"
        obj.freecad_version = "{}.{}".format(*app.Version())
        app.Console.PrintWarning("updating {} from openglider 0.01 to openglider 0.02\n".format(obj.Label))

def from_0_02_to_0_03(obj):
    if obj.openglider_version == "0.02":
        if hasattr(obj, "horizontal_shift"):
            value = obj.horizontal_shift
            obj.removeProperty("horizontal_shift")
            addProperty(obj, 'vertical_shift', value, 'hole', 'relative vertical shift')
        obj.openglider_version = "0.03"
        app.Console.PrintWarning("updating {} from openglider 0.02 to openglider 0.03\n".format(obj.Label))


