import FreeCADGui as Gui

Gui.addIconPath(FreeCAD.getHomePath() + "Mod/glider_gui/icons")

from tools import (CreateGlider, Shape_Tool,
                   Airfoil_Tool, Arc_Tool, Aoa_Tool,
                   Ballooning_Tool, Line_Tool, Attach_Tool)


Gui.addCommand('CreateGlider', CreateGlider())
Gui.addCommand('Shape_Tool', Shape_Tool())
Gui.addCommand('Airfoil_Tool', Airfoil_Tool())
Gui.addCommand('Arc_Tool', Arc_Tool())
Gui.addCommand("Aoa_Tool", Aoa_Tool())
Gui.addCommand("Ballooning_Tool", Ballooning_Tool())
Gui.addCommand("Attach_Tool", Attach_Tool())
Gui.addCommand("Line_Tool", Line_Tool())


class gliderWorkbench(Workbench):
    """probe workbench object"""
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"
    profileitems = [
        "CreateGlider",
        "Shape_Tool",
        "Arc_Tool",
        "Aoa_Tool",
        "Airfoil_Tool",
        "Ballooning_Tool",
        "Attach_Tool",
        "Line_Tool"]

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        self.appendToolbar("Glider", self.profileitems)
        self.appendMenu("Glider", self.profileitems)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(gliderWorkbench())