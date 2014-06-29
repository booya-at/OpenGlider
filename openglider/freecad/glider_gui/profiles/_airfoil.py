import FreeCAD
from pivy import coin
from openglider.airfoil import Profile2D
import PartGui

class _Airfoil(object):
    """FreeCAD Airfoil"""

    def __init__(self, obj):
        obj.addProperty("App::PropertyPythonObject", "prof", "test", "test").prof = Profile2D.compute_naca()
        obj.addProperty("App::PropertyString", "Name", "airfoil", "Name of airfoil").Name = obj.prof.name
        obj.addProperty("App::PropertyPath", "FilePath", "airfoil", "Name of airfoil").FilePath = ""
        obj.Proxy = self

    def execute(self, fp):
        pass

    def onChanged(self, fp, prop):
        if prop == "FilePath":
            fp.prof = Profile2D.import_from_dat(fp.FilePath)
            fp.name = fp.prof.name


class ViewProviderAirfoil(object):
    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyLength", "LineWidth", "Base", "Line width")
        obj.addProperty(
            "App::PropertyColor", "LineColor", "Base", "Line color")
        self.obj = obj.Object
        obj.Proxy = self

    def attach(self, vobj):
        self.shaded = coin.SoSeparator()
        t = coin.SoType.fromName("SoBrepEdgeSet")
        self.lineset = t.createInstance()

        self.lineset.highlightIndex = -1
        self.lineset.selectionIndex = 0
        self.color = coin.SoBaseColor()
        c = vobj.LineColor
        self.color.rgb.setValue(c[0], c[1], c[2])
        self.drawstyle = coin.SoDrawStyle()
        self.drawstyle.lineWidth = 1
        self.data = coin.SoCoordinate3()
        self.shaded.addChild(self.color)
        self.shaded.addChild(self.drawstyle)
        self.shaded.addChild(self.data)
        self.shaded.addChild(self.lineset)
        vobj.addDisplayMode(self.shaded, 'Shaded')
        pass

    def execute(self, fp):
        self.updateData(fp, "FilePath")

    def updateData(self, fp, prop):
        """Update geometry"""
        if prop == "prof":
            points = self.profilepoints(fp.prof.data)
            self.data.point.setValue(0, 0, 0)
            self.data.point.setValues(0, len(points), points)
            nums = range(len(points))
            self.lineset.coordIndex.setValue(0)
            self.lineset.coordIndex.setValues(0, len(nums), nums)

    def getElement(self, detail):
        if detail.getTypeId() == coin.SoLineDetail.getClassTypeId():
            line_detail = coin.cast(detail, str(detail.getTypeId().getName()))
            edge = line_detail.getLineIndex() + 1
            return "Edge" + str(edge)

    def onChanged(self, vp, prop):
        if prop == "LineWidth":
            self.drawstyle.lineWidth = vp.LineWidth
        if prop == "LineColor":
            c = vp.LineColor
            self.color.rgb.setValue(c[0], c[1], c[2])
        pass

    def getDisplayModes(self, obj):
        """Return a list of display modes."""
        modes = ["Shaded"]
        return modes

    def profilepoints(self, points):
        return map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), points)