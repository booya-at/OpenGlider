import FreeCADGui as Gui
import gliderGui


class gliderWorkbench(Workbench):
    """probe workbench object"""
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        profileitems = ["CreatePoint", "Airfoil"]
        self.appendToolbar("test", profileitems)
        self.appendMenu("test", profileitems)

    def Activated(self):
        pass

    def Deactivated(self):
        pass


Gui.addWorkbench(gliderWorkbench())
