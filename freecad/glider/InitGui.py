import FreeCADGui as Gui
import FreeCAD
import gliderGui


class gliderWorkbench(Workbench):
    """probe workbench object"""
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"

    def GetClassName(self):
        return "gliderGui::Workbench"

    def Initialize(self):
        #load the module
        self.appendToolbar("Glider", ["LoadGlider","ChangeShape"])
        self.appendMenu("Glider", ["LoadGlider","ChangeShape"])

        profileitems=["LoadProfile", "ChangeProfile", "CompareProfile", "MergeProfile", "RunXfoil"]
        self.appendToolbar("Profile", profileitems)
        self.appendMenu("Profile", profileitems)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(gliderWorkbench())

# Append the open handler
#FreeCAD.EndingAdd("probe formats (*.bmp *.jpg *.png *.xpm)","probeGui")
