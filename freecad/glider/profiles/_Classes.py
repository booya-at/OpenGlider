import FreeCAD
from Profile import Profile2D
from pivy import coin
import PartGui


class Airfoil():
    """FreeCAD Airfoil"""
    def __init__(self, obj):
        self.prof = Profile2D()

        obj.addProperty("App::PropertyInteger", "Numpoints", "profile", "Number of points").Numpoints = self.prof.Numpoints
        obj.addProperty("App::PropertyFloat", "Thickness", "profile", "Thickness of Profile").Thickness = max(self.prof.Thickness[:,1]) * 1000
        obj.addProperty("App::PropertyFloat", "Camber", "profile", "Camber of Profile").Camber = max(self.prof.Camber[:,1]) * 1000
        obj.addProperty("App::PropertyString", "Name", "profile", "Name of profile").Name = self.prof.Name
        obj.addProperty("App::PropertyVectorList", "coords", "profile", "profilcoords")
        obj.addProperty("App::PropertyPath", "FilePath", "profile", "Name of profile").FilePath = ""
        obj.Proxy = self

    def execute(self, fp):
        self.prof.Numpoints = fp.Numpoints
        self.prof.Thickness = fp.Thickness / 1000.
        self.prof.Camber = fp.Camber / 1000.
        self.prof.Name=fp.Name
        fp.coords = map(lambda x: FreeCAD.Vector(x[0],x[1],0.),self.prof.Profile)


    def onChanged(self, fp, prop):
        if prop == "FilePath":
            FreeCAD.Console.PrintMessage("1")
            self.prof.Import(fp.FilePath)
            fp.Numpoints = self.prof.Numpoints
            fp.Thickness = max(self.prof.Thickness[:,1]) *1000.
            fp.Camber = max(self.prof.Camber[:,1]) *1000.
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Thickness":
            FreeCAD.Console.PrintMessage("2")
            self.prof.Thickness = fp.Thickness / 1000.
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Numpoints":
            FreeCAD.Console.PrintMessage("3")
            self.prof.Numpoints = fp.Numpoints
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Camber":
            FreeCAD.Console.PrintMessage("4")
            self.prof.Camber = fp.Camber /1000.
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)




class ViewProviderAirfoil():
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","LineWidth","Base","Line width")
        obj.addProperty("App::PropertyColor","LineColor","Base","Line color")
        obj.Proxy = self

    def attach(self, vobj):
        self.shaded = coin.SoSeparator()
        t = coin.SoType.fromName("SoBrepEdgeSet")
        self.panels = t.createInstance()
        self.color = coin.SoBaseColor()
        c=vobj.LineColor
        self.color.rgb.setValue(c[0], c[1], c[2])
        self.drawstyle = coin.SoDrawStyle()
        self.drawstyle.lineWidth = 1
        self.style = coin.SoDrawStyle()
        self.data = coin.SoCoordinate3()
        self.shaded.addChild(self.color)
        self.shaded.addChild(self.drawstyle)
        self.shaded.addChild(self.data)
        self.shaded.addChild(self.panels)
        vobj.addDisplayMode(self.shaded, 'Shaded')

    def updateData(self, fp, prop):
        'jkhjkn'
        if prop == "coords":
            s = fp.getPropertyByName("coords")
            pts = s
            self.data.point.setValue(0,0,0)
            self.data.point.setValues(0 , len(pts),pts)
            nums = []
            numPoints = len(pts)
            for i in range(numPoints):
                nums.append(i)
                nums.append((i+1)%numPoints)
                nums.append(-1)
            self.panels.coordIndex.setValue(0)
            self.panels.coordIndex.setValues(0,len(nums), nums)

    def onChanged(self, vp, prop):
        if prop == "LineWidth":
            self.drawstyle.lineWidth = vp.LineWidth
        if prop == "LineColor":
            c = vp.LineColor
            self.color.rgb.setValue(c[0], c[1], c[2])


    def getDisplayModes(self,obj):
        "Return a list of display modes."
        modes=[]
        modes.append("Shaded")
        return modes



from Utils.Bezier import BezierCurve
class BezierCurve(BezierCurve):
    def __init__(self, obj, coords=None):
        """a bspline object that can be used to change shapes like airfoils"""
        if not coords: coords = [[0., 0.], [1., 1.], [2., 0.], [2., 1.]]
        BezierCurve.__init__(self,coords)
        obj.addProperty("App::PropertyInteger", "beziernumpoints", "bezier", "number of bezierpoints").beziernumpoints = self.numofbezierpoints
        obj.addProperty("App::PropertyVectorList", "bezierpoints", "bezier", "bezierpoints").bezierpoints = self.BezierPoints
        obj.addProperty("App::PropertyInteger", "numlinepoints", "line", "number of points").numpoints = self.numpoints
        obj.addProperty("App::PropertyVectorList", "linepoints", "line", "store")
        obj.Proxy = self

    def execute(self, fp):
        self.numofbezierpoints = fp.beziernumpoints
        fp.linepoints = self.getPoints()

    def onChanged(self, fp, prop):
        pass
