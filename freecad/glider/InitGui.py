import FreeCADGui as Gui
import FreeCAD
import gliderGui


class gliderWorkbench(Workbench):
    "probe workbench object"
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"

    def GetClassName(self):
        return "gliderGui::Workbench"

    def Initialize(self):
        #load the module
        self.appendToolbar("Glider", ["LoadGlider","ChangeShape"])
        self.appendMenu("Glider", ["LoadGlider","ChangeShape"])

        self.appendToolbar("Profile", ["LoadProfile", "ChangeProfile"])
        self.appendMenu("Profile", ["LoadProfile", "ChangeProfile"])

    def Activated(self):
        FreeCAD.Console.PrintMessage('hello')

    def Deactivated(self):
        FreeCAD.Console.PrintMessage('hello')

    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(gliderWorkbench())

# Append the open handler
#FreeCAD.EndingAdd("probe formats (*.bmp *.jpg *.png *.xpm)","probeGui")
