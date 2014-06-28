import FreeCAD
import FreeCADGui as Gui
from _Classes import Line, VpLine

class CreatePoint:
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'glider_obj_point.svg', 'MenuText': 'Point', 'ToolTip': 'Point'}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Line")
        Line(a, [(1,1,1),(2,3,3)])
        VpLine(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()