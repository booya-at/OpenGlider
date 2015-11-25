import FreeCADGui as Gui
import FreeCAD

from tools import *

Gui.addIconPath(FreeCAD.ConfigGet("UserAppData") + "/Mod/glider_gui/icons")

Gui.addCommand('CreateGlider', CreateGlider())
Gui.addCommand('Shape_Tool', Shape_Tool())
Gui.addCommand('Airfoil_Tool', Airfoil_Tool())
Gui.addCommand('Arc_Tool', Arc_Tool())
Gui.addCommand("Aoa_Tool", Aoa_Tool())
Gui.addCommand("Ballooning_Tool", Ballooning_Tool())
Gui.addCommand("Line_Tool", Line_Tool())
Gui.addCommand("Gl2d_Import", Gl2d_Import())
Gui.addCommand("Gl2d_Export", Gl2d_Export())
Gui.addCommand("AirfoilMergeTool", AirfoilMergeTool())
Gui.addCommand("BallooningMergeTool", BallooningMergeTool())


Gui.addCommand("Pattern_Tool", Pattern_Tool())
Gui.addCommand("Panel_Tool", Panel_Tool())
Gui.addCommand("Polars_Tool", Polars_Tool())

Gui.addCommand("Reload", Reload())


class gliderWorkbench(Workbench):
    """probe workbench object"""
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"
    toolbox = [
        "CreateGlider",
        "Gl2d_Import",
        "Shape_Tool",
        "Arc_Tool",
        "Aoa_Tool",
        "Airfoil_Tool",
        "AirfoilMergeTool",
        "Ballooning_Tool",
        "BallooningMergeTool",
        "Line_Tool",
        "Gl2d_Export"]

    productionbox = [
        "Pattern_Tool",
        "Panel_Tool",
        "Polars_Tool",
        "Reload"
        ]


    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        self.appendToolbar("Tools", self.toolbox)
        self.appendMenu("Tools", self.toolbox)
        self.appendToolbar("Production", self.productionbox)
        self.appendMenu("Production", self.productionbox)

    def Activated(self):
        pass

    def Deactivated(self):
        pass


try:
    from tools import Panel_Tool

except ImportError:
    pass

Gui.addWorkbench(gliderWorkbench())