import FreeCADGui as Gui

Gui.addIconPath(FreeCAD.getHomePath() + "Mod/glider_gui/icons")

from objects import CreateGlider, Shape_Tool, Airfoil_Tool

Gui.addCommand('CreateGlider', CreateGlider())
Gui.addCommand('Shape_Tool', Shape_Tool())
Gui.addCommand('Airfoil_Tool', Airfoil_Tool())

class gliderWorkbench(Workbench):
    """probe workbench object"""
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        profileitems = ["CreateGlider", "Shape_Tool", "Airfoil_Tool"]
        self.appendToolbar("test", profileitems)
        self.appendMenu("test", profileitems)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(gliderWorkbench())