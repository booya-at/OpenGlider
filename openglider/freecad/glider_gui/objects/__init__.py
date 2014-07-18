import FreeCAD
import FreeCADGui as Gui
from _base import OGLine, OGLineVP, OGSpline, OGSplineVP
from shape import OGShape, OGShapeVP, OGSymSplineVP
from _glider import OGGlider, OGGliderVP
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


class CreateLine(BaseCommand):
    def GetResources(self):
        return {'Pixmap': "glider_import.svg", 'MenuText': 'glider', 'ToolTip': 'glider'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Line")
        OGGlider(a)
        OGGliderVP(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()


class CreateSpline(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_obj_point.svg', 'MenuText': 'Line', 'ToolTip': 'Line'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Spline")
        OGSpline(a, [(1,1,0),(2,0,0),(3,1,0),(4,0,0)])
        OGSplineVP(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()


class CreateShape(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_obj_point.svg', 'MenuText': 'Line', 'ToolTip': 'Line'}

    def Activated(self):
        upper =  FreeCAD.ActiveDocument.addObject("App::FeaturePython", "upper")
        lower = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "lower")
        OGSpline(upper, [(1,1,0),(2,1,0),(3,1,0),(4,1,0)])
        OGSpline(lower, [(1,0,0),(2,0,0),(3,0,0),(4,0,0)])
        OGSymSplineVP(upper.ViewObject)
        OGSymSplineVP(lower.ViewObject)
        shape = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Shape")
        OGShape(shape, upper, lower)
        OGShapeVP(shape.ViewObject)
        FreeCAD.ActiveDocument.recompute()


class Airfoil(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'glider_profile_compare.svg', 'MenuText': 'Airfoil', 'ToolTip': 'Airfoil'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Airfoil")
        _Airfoil(a)
        ViewProviderAirfoil(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
