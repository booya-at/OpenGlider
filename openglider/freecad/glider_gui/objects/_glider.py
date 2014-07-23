from __future__ import division
import openglider
from pivy import coin
import FreeCAD
from pivy_primitives import Line

importpath = "/home/q/tmp/OpenGlider/tests/demokite.ods"


class OGBaseObject(object):
    def __init__(self, obj):
        obj.Proxy = self

    def execute(self, fp):
        pass


class OGBaseVP(object):
    def __init__(self, obj):
        obj.Proxy = self

    def attach(self, vobj):
        pass

    def updateData(self, fp, prop):
        pass

    def getDisplayModes(self, obj):
        mod = ["out"]
        return(mod)


class OGGlider(OGBaseObject):
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyPythonObject", "glider_instance", "object", "glider_instance")
        obj.glider_instance = openglider.glider.Glider.import_geometry(path=importpath)
        super(OGGlider, self).__init__(obj)


class OGGliderVP(OGBaseVP):
    def __init__(self, view_obj):
        view_obj.addProperty(
            "App::PropertyInteger", "num_ribs", "num_ribs", "num_ribs")
        view_obj.num_ribs = 0
        self.vis_glider = coin.SoSeparator()
        self.vis_lines = coin.SoSeparator()
        self.material = coin.SoMaterial()
        self.seperator = coin.SoSeparator()
        self.view_obj = view_obj
        self.glider_instance = view_obj.Object.glider_instance
        super(OGGliderVP, self).__init__(view_obj)

    def attach(self, vobj):
        # self.vertexproperty.orderedRGBA = coin.SbColor(.7, .7, .7).getPackedValue()
        self.material.diffuseColor = (.7, .7, .7)
        self.seperator.addChild(self.vis_glider)
        self.seperator.addChild(self.vis_lines)
        self.seperator.addChild(self.material)
        vobj.addDisplayMode(self.seperator, 'out')

    def updateData(self, fp=None, prop=None):
        self.update_glider(self.view_obj.num_ribs)
        self.update_lines()

    def update_glider(self, midrips=0):
        self.vis_glider.removeAllChildren()
        glider = self.glider_instance.copy_complete()
        if midrips == 0:
            vertexproperty = coin.SoVertexProperty()
            mesh = coin.SoQuadMesh()
            ribs = glider.ribs
            flat_coords = [i for rib in ribs for i in rib.profile_3d.data]
            vertexproperty.vertex.setValues(0, len(flat_coords), flat_coords)
            mesh.verticesPerRow = len(ribs[0].profile_3d.data)
            mesh.verticesPerColumn = len(ribs)
            mesh.vertexProperty = vertexproperty
            self.vis_glider.addChild(mesh)
            self.vis_glider.addChild(vertexproperty)
        else:
            for cell in glider.cells:
                sep = coin.SoSeparator()
                vertexproperty = coin.SoVertexProperty()
                mesh = coin.SoQuadMesh()
                ribs = [cell.midrib(pos / (midrips + 1)) for pos in range(midrips + 2)]
                flat_coords = [i for rib in ribs for i in rib]
                vertexproperty.vertex.setValues(0, len(flat_coords), flat_coords)
                mesh.verticesPerRow = len(ribs[0])
                mesh.verticesPerColumn = len(ribs)
                mesh.vertexProperty = vertexproperty
                sep.addChild(vertexproperty)
                sep.addChild(mesh)
                self.vis_glider.addChild(sep)


    def update_lines(self):
        self.vis_lines.removeAllChildren()
        for l in self.glider_instance.lineset.lines:
            sep = Line(l.get_line_points()).object
            self.vis_lines.addChild(sep)

    def getIcon(self):
        return FreeCAD.getHomePath() + "Mod/glider_gui/icons/glider_import.svg"





# parametric_glider = {
#     "shape": {
#         "leading_edge": [],
#         "trailing_edge": []
#     },
#     "arc": [],
#     "aoa": [],
#     "rotate": [],
#     "profile": [
#         {
#             "name": "superprofil",
#             "data": []
#         }
#     ],
#     "balooning": [],
# 	"profile_merge": [],
# 	"balloning_merge": [],

# }
