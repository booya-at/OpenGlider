import FreeCAD
import FreeCADGui as Gui

from _glider import OGGlider, OGGliderVP
from _tools import (shape_tool, base_tool, ballooning_tool,
                    arc_tool, aoa_tool, airfoil_tool)
from attach_tool import attach_tool
from line_tool import line_tool


#ICONS:
# the openglider implementation in freecad will be splitted into 3 parts. each will have a consistent icon color-sheme:
# (colors can be found in openglider/freecad/glidergui/icons/freecad-color.gpl)
# to use this with inkscape: ln -s ..../openglider/freecad/glidergui/icons/freecad-color.gpl .../.config/inkscape/palettes/

#   -import export                                          -?
#   -construction (shape, arc, lines, aoa, ...)             -blue
#   -simulation                                             -yellow
#   -optimisation                                           -red


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
        obj = Gui.Selection.getSelection()
        if len(obj) > 0:
            obj = obj[0]
            if check_glider(obj):
                test = Gui.Control.showDialog(self.tool(obj))

    def tool(self, obj):
        return base_tool(obj)


class CreateGlider(BaseCommand):
    def GetResources(self):
        return {'Pixmap': "new_glider.svg", 'MenuText': 'glider', 'ToolTip': 'glider'}

    def Activated(self):
        a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Glider")
        OGGlider(a)
        OGGliderVP(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()
        Gui.SendMsgToActiveView("ViewFit")


class Shape_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'shape_tool.svg', 'MenuText': 'Shape', 'ToolTip': 'Shape'}

    def tool(self, obj):
        return shape_tool(obj)


class Arc_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'arc_tool.svg', 'MenuText': 'Arc', 'ToolTip': 'Arc'}

    def tool(self, obj):
        print("jojojo")
        return arc_tool(obj)


class Aoa_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'aoa_tool.svg', 'MenuText': 'Aoa', 'ToolTip': 'Aoa'}

    def tool(self, obj):
        return aoa_tool(obj)


class Airfoil_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'airfoil_tool.svg', 'MenuText': 'Airfoil', 'ToolTip': 'Airfoil'}

    def tool(self, obj):
        return airfoil_tool(obj)


class Ballooning_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'ballooning_tool.svg', 'MenuText': 'Ballooning', 'ToolTip': 'Ballooning'}

    def tool(self, obj):
        return ballooning_tool(obj)

class Attach_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'attach_tool.svg', 'MenuText': 'Attachmentpoints', 'ToolTip': 'Attachmentpoints'}

    def tool(self, obj):
        return attach_tool(obj)


class Line_Tool(BaseCommand):
    def GetResources(self):
        return {'Pixmap': 'line_tool.svg', 'MenuText': 'Lines', 'ToolTip': 'Lines'}

    def tool(self, obj):
        return line_tool(obj)


def check_glider(obj):
    if "glider_instance" in obj.PropertiesList and "glider_2d" in obj.PropertiesList:
        return True
    else:
        return False


