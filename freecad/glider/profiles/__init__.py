import FreeCAD
from _Classes import Airfoil, ViewProviderAirfoil



class LoadProfile:
    def __init__(self):
        pass

    def GetResources(self):
        return {'Pixmap': 'glider_import_profile.svg', 'MenuText': 'load profile', 'ToolTip': 'load profile'}
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    def Activated(self):
        a=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Profile")
        Airfoil(a)
        ViewProviderAirfoil(a.ViewObject)
        FreeCAD.ActiveDocument.recompute()

class ChangeProfile:
    def __init__(self):
        pass
    def GetResources(self):
        return {'Pixmap': 'glider_change_profile.svg', 'MenuText': 'change profiles', 'ToolTip': 'change profiles'}
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    def Activated(self):
        pass

class RunXfoil:
    def __init__(self):
        pass
    def GetResources(self):
        return {'Pixmap': 'glider_profile_xfoil.svg', 'MenuText': 'run xfoil', 'ToolTip': 'run xfoil'}
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    def Activated(self):
        pass

class CompareProfile:
    def __init__(self):
        pass
    def GetResources(self):
        return {'Pixmap': 'glider_profile_compare.svg', 'MenuText': 'compare profile', 'ToolTip': 'compare profile'}
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    def Activated(self):
        pass


class MergeProfile:
    def __init__(self):
        pass
    def GetResources(self):
        return {'Pixmap': 'glider_profile_merge.svg', 'MenuText': 'merge profile', 'ToolTip': 'merge profile'}
    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True
    def Activated(self):
        pass


