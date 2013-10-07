import FreeCAD
try:
    from Profile import Profile2D
except:
    import sys
    sys.path.append('/home/lo/Openglider/')
    from Profile import Profile2D
import Draft
import numpy as np
import Part


class LoadProfile:
    def GetResources(self):
        return {'Pixmap': 'glider_import_profile.svg', 'MenuText': 'load profile', 'ToolTip': 'load profile'}
    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True
    def Activated(self):
        FreeCAD.Console.PrintWarning('das teil kann nix')

class ChangeProfile:
    def GetResources(self):
        return {'Pixmap': 'glider_change_profile.svg', 'MenuText': 'change profiles', 'ToolTip': 'change profiles'}
    def IsActive(self):
        if FreeCAD.ActiveDocument == None:
            return False
        else:
            return True
    def Activated(self):
        FreeCAD.Console.PrintError('das teil kann nix')

class Profile(Profile2D):
    def __init__(self, obj,path,numpoints=100):
        Profile2D.__init__(self,path)
        self.Import(path)
        self.Numpoints=numpoints
        obj.addProperty("App::PropertyInteger","Numpoints","Line","End point").Numpoints=numpoints
        obj.Proxy = self

    def execute(self, fp):
        "Print a short message when doing a recomputation, this method is mandatory"
        pro=self.Profile
        pro=pro.tolist()
        pro=map(lambda x: FreeCAD.Vector(x[0],x[1],0.),pro)
        print(pro)
        edges = []
        pts = pro[1:]

        lp = pro[0]
        for p in pts:
            edges.append(Part.Line(lp,p).toShape())
            lp = p
        shape = Part.Wire(edges)
        fp.Shape = shape