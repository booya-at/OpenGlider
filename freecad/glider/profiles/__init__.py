import FreeCAD
from _Classes import *
import FreeCADGui
from pivy.coin import SoMouseButtonEvent, SoLocation2Event




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
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.x=False
        self.y=False
        self.createcallback = self.view.addEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self._makepoint)  
        FreeCAD.ActiveDocument.recompute()  

    def _makepoint(self,event_cb):
        event = event_cb.getEvent()
        if event.getState() == SoMouseButtonEvent.DOWN:
            pos = event.getPosition()
            point = self.view.getPoint(pos[0],pos[1])
            self.x=point[0]
            self.y=point[1]
            if self.x != False and self.y!=False:
                self.a=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Point")
                moveablePoint(self.a, self.x, self.y)
                ViewProvidermoveablePoint(self.a.ViewObject)
                self.view.removeEventCallbackPivy(SoMouseButtonEvent.getClassTypeId(),self.createcallback)    


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
        self.b=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Line")
        self.ml = moveableLine(self.b, [])
        ViewProvidermoveableLine(self.b.ViewObject)
        self.a1 = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Point")
        moveablePoint(self.a1, 1., 1.)
        ViewProvidermoveablePoint(self.a1.ViewObject, self.ml)
        self.a2=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Point")
        moveablePoint(self.a2, 2., 2.)
        ViewProvidermoveablePoint(self.a2.ViewObject, self.ml)
        self.a3=FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Point")
        moveablePoint(self.a3, 2., 0.)
        ViewProvidermoveablePoint(self.a3.ViewObject, self.ml)
        self.ml.addObject(self.a1)
        self.ml.addObject(self.a2)
        self.ml.addObject(self.a3)



    def updatelist(self):
        for i in self.b.Object.points:
            if i.Object.ischanged:
                self.b.Object.ViewObject.x1=0.


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
        self.a = FreeCAD.ActiveDocument.addObject("App::FeaturePython", "Points")
        moveablepoints(self.a, [[1., 1.],[0.,0.],[3.,3.]])
        ViewProvidermoveablepoints(self.a.ViewObject)
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

