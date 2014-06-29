import FreeCAD
import FreeCADGui as Gui
from _Classes import Line, VpLine
from _airfoil import _Airfoil, ViewProviderAirfoil

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


class CreatePoint(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_obj_point.svg', 'MenuText': 'Point', 'ToolTip': 'Point'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Line")
        Line(a, [(1,1,1),(2,3,3),(10,10,2),(4,4,4)])
        VpLine(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()


class Airfoil(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_profile_compare.svg', 'MenuText': 'Airfoil', 'ToolTip': 'Airfoil'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Airfoil")
        _Airfoil(a)
        ViewProviderAirfoil(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
