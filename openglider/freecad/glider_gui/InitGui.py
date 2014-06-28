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
        profileitems = ["CreatePoint"]
        self.appendToolbar("test", profileitems)
        self.appendMenu("test", profileitems)

    def Activated(self):
        pass

    def Deactivated(self):
        pass


Gui.addWorkbench(gliderWorkbench())

# Append the open handler
#FreeCAD.EndingAdd("probe formats (*.bmp *.jpg *.png *.xpm)","probeGui")
