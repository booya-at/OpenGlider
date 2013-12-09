import FreeCAD

class ChangeShape:
    def GetResources(self):
        return {'Pixmap': 'glider_change_shape.svg', 'MenuText': 'change shape', 'ToolTip': 'change shape'}
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    def Activated(self):
        FreeCAD.Console.PrintMessage('das teil kann nix')