import FreeCAD
import FreeCADGui as Gui
from _glider import OGGlider, OGGliderVP
from _tools import shape_tool, airfoil_tool


class BaseCommand(object):
    def __init__(self):
        pass

    def GetResources(self):
        """return {'Pixmap': '.svg', 'MenuText': 'Text', 'ToolTip': 'Text'}"""
        pass

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        pass


class CreateGlider(BaseCommand):
    def GetResources(self):
        return {'Pixmap': "glider_import.svg", 'MenuText': 'glider', 'ToolTip': 'glider'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Glider")
        OGGlider(a)
        OGGliderVP(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()


class Shape_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_profile_compare.svg', 'MenuText': 'base', 'ToolTip': 'base'}

    def Activated(self):
        obj = Gui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                bt = shape_tool(obj)
                Gui.Control.showDialog(bt)
            else:
                pass

class Airfoil_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_profile_compare.svg', 'MenuText': 'base', 'ToolTip': 'base'}

    def Activated(self):
        obj = Gui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                bt = airfoil_tool(obj)
                Gui.Control.showDialog(bt)
            else:
                pass


def check_glider(obj):
    if "glider_instance" in obj.PropertiesList:
        return True
    else:
        return False