import FreeCAD
from OpenGlider.Profile import Profile2D
from pivy import coin
import PartGui


class Airfoil():
    """FreeCAD Airfoil"""
    def __init__(self, obj):
        self.prof = Profile2D()

        obj.addProperty("App::PropertyInteger", "Numpoints", "profile", "Number of points").Numpoints = self.prof.Numpoints
        obj.addProperty("App::PropertyFloat", "Thickness", "profile", "Thickness of Profile").Thickness = max(self.prof.Thickness[:,1]) * 1000
        #obj.addProperty("App::PropertyFloat", "Camber", "profile", "Camber of Profile").Camber = max(self.prof.Camber[:,1]) * 1000
        obj.addProperty("App::PropertyString", "Name", "profile", "Name of profile").Name = self.prof.name
        obj.addProperty("App::PropertyVectorList", "coords", "profile", "profilcoords")
        obj.addProperty("App::PropertyPath", "FilePath", "profile", "Name of profile").FilePath = ""
        obj.Proxy = self

    def execute(self, fp):
        self.prof.Numpoints = fp.Numpoints
        self.prof.Thickness = fp.Thickness / 1000.
        #self.prof.Camber = fp.Camber / 1000.
        self.prof.name=fp.Name
        fp.coords = map(lambda x: FreeCAD.Vector(x[0],x[1],0.),self.prof.Profile)
        pass


    def onChanged(self, fp, prop):
        if prop == "FilePath":
            FreeCAD.Console.PrintMessage("1")
            self.prof.importdat(fp.FilePath)
            fp.Numpoints = self.prof.Numpoints
            fp.Thickness = max(self.prof.Thickness[:, 1]) *1000.
            #fp.Camber = max(self.prof.Camber[:, 1]) *1000.
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Thickness":
            FreeCAD.Console.PrintMessage("2")
            self.prof.Thickness = fp.Thickness / 1000.
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        # elif prop == "Numpoints":
        #     FreeCAD.Console.PrintMessage("3")
        #     self.prof.Numpoints = fp.Numpoints
        #     fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Camber":
            FreeCAD.Console.PrintMessage("4")
            self.prof.Camber = fp.Camber /1000.
            fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        pass




class ViewProviderAirfoil():
    def __init__(self, obj):
        obj.addProperty("App::PropertyLength","LineWidth","Base","Line width")
        obj.addProperty("App::PropertyColor","LineColor","Base","Line color")
        obj.Proxy = self

    def attach(self, vobj):
        self.shaded = coin.SoSeparator()
        t = coin.SoType.fromName("SoBrepEdgeSet")
        self.lineset = t.createInstance()
        self.lineset.highlightIndex = -1
        self.lineset.selectionIndex = 0
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
        self.shaded.addChild(self.lineset)
        vobj.addDisplayMode(self.shaded, 'Shaded')
        pass

    def updateData(self, fp, prop):
        'jkhjkn'
        if prop == "coords":
            points = fp.getPropertyByName("coords")
            self.data.point.setValue(0,0,0)
            self.data.point.setValues(0 , len(points),points)
            nums = range(len(points))
            self.lineset.coordIndex.setValue(0)
            self.lineset.coordIndex.setValues(0,len(nums), nums)
        pass

    def getElement(self,detail):
        if detail.getTypeId() == coin.SoLineDetail.getClassTypeId():
            line_detail = coin.cast(detail,str(detail.getTypeId().getName()))
            edge = line_detail.getLineIndex() + 1
            return "Edge" + str(edge)

    def onChanged(self, vp, prop):
        if prop == "LineWidth":
            self.drawstyle.lineWidth = vp.LineWidth
        if prop == "LineColor":
            c = vp.LineColor
            self.color.rgb.setValue(c[0], c[1], c[2])
        pass


    def getDisplayModes(self,obj):
        "Return a list of display modes."
        modes=[]
        modes.append("Shaded")
        return modes
        pass



# from Utils.Bezier import BezierCurve
# class BezierCurve(BezierCurve):
#     def __init__(self, obj, coords=None):
#         """a bspline object that can be used to change shapes like airfoils"""
#         if not coords: coords = [[0., 0.], [1., 1.], [2., 0.], [2., 1.]]
#         BezierCurve.__init__(self,coords)
#         obj.addProperty("App::PropertyInteger", "beziernumpoints", "bezier", "number of bezierpoints").beziernumpoints = self.numofbezierpoints
#         obj.addProperty("App::PropertyVectorList", "bezierpoints", "bezier", "bezierpoints").bezierpoints = self.BezierPoints
#         obj.addProperty("App::PropertyInteger", "numlinepoints", "line", "number of points").numpoints = self.numpoints
#         obj.addProperty("App::PropertyVectorList", "linepoints", "line", "store")
#         obj.Proxy = self

#     def execute(self, fp):
#         self.numofbezierpoints = fp.beziernumpoints
#         fp.linepoints = self.getPoints()

#     def onChanged(self, fp, prop):
#         pass
