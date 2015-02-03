from __future__ import division
import os

from pivy import coin
import FreeCAD


import openglider
from openglider.glider import Glider, Glider2D
from openglider.jsonify import load
from pivy_primitives import Line

importpath = os.path.join(os.path.dirname( __file__ ), '..', 'demokite.ods')
print(importpath)

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

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None


class OGGlider(OGBaseObject):
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyPythonObject", "glider_instance", "object", "glider_instance")
        obj.addProperty(
            "App::PropertyPythonObject", "glider_2d", "object", "parametric glider")
        print(str(FreeCAD.getHomePath()) + "/Mod/glider_gui/glider2d.json")
        with open(str(FreeCAD.getHomePath()) + "Mod/glider_gui/glider2d.json", 'r') as importfile:
            obj.glider_2d = load(importfile)["data"]
        obj.glider_instance = obj.glider_2d.get_glider_3d()
        super(OGGlider, self).__init__(obj)


class OGGliderVP(OGBaseVP):
    def __init__(self, view_obj):
        view_obj.addProperty(
            "App::PropertyInteger", "num_ribs", "accuracy", "num_ribs")
        view_obj.addProperty(
            "App::PropertyInteger", "profile_num", "accuracy", "profile_num")
        view_obj.num_ribs = 0
        view_obj.profile_num = 13        
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
        if prop in ["num_ribs", "profile_num", None]:
            self.update_glider(midribs=self.view_obj.num_ribs, profile_numpoints=self.view_obj.profile_num)
        # self.update_lines()

    def update_glider(self, midribs=0, profile_numpoints=20):
        self.vis_glider.removeAllChildren()
        glider = self.glider_instance.copy_complete()
        glider.profile_numpoints = profile_numpoints
        if midribs == 0:
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
                ribs = [cell.midrib(pos / (midribs + 1)) for pos in range(midribs + 2)]
                flat_coords = [i for rib in ribs for i in rib]
                vertexproperty.vertex.setValues(0, len(flat_coords), flat_coords)
                mesh.verticesPerRow = len(ribs[0])
                mesh.verticesPerColumn = len(ribs)
                mesh.vertexProperty = vertexproperty
                sep.addChild(vertexproperty)
                sep.addChild(mesh)
                self.vis_glider.addChild(sep)
        self.vis_lines.removeAllChildren()
        for line in glider.lineset.lines:
            points = line.get_line_points()
            self.vis_glider.addChild(Line([[i[0], -i[1], i[2]] for i in points]).object)
            self.vis_lines.addChild(Line(points).object)

    def onChanged(self, vp, prop):
        self.updateData()

    def getIcon(self):
        return str(FreeCAD.getHomePath() + "Mod/glider_gui/icons/glider_import.svg")

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
