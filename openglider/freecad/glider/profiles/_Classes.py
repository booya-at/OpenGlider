import FreeCAD
import FreeCADGui
from openglider.Profile import Profile2D
from pivy import coin
import PartGui
import numpy


class Airfoil():

    """FreeCAD Airfoil"""

    def __init__(self, obj):
        self.prof = Profile2D()

        obj.addProperty("App::PropertyInteger", "Numpoints",
                        "profile", "Number of points").Numpoints = self.prof.Numpoints
        obj.addProperty("App::PropertyFloat", "Thickness", "profile",
                        "Thickness of Profile").Thickness = self.prof.Thickness * 1000
        #obj.addProperty("App::PropertyFloat", "Camber", "profile", "Camber of Profile").Camber = max(self.prof.Camber[:,1]) * 1000
        obj.addProperty("App::PropertyString", "Name",
                        "profile", "Name of profile").Name = self.prof.name
        obj.addProperty(
            "App::PropertyVectorList", "coords", "profile", "profilcoords")
        obj.addProperty("App::PropertyPath", "FilePath",
                        "profile", "Name of profile").FilePath = ""
        obj.Proxy = self

    def execute(self, fp):
        self.prof.Numpoints = fp.Numpoints
        self.prof.Thickness = fp.Thickness / 1000.
        #self.prof.Camber = fp.Camber / 1000.
        self.prof.name = fp.Name
        fp.coords = map(
            lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        pass

    def onChanged(self, fp, prop):
        if prop == "FilePath":
            self.prof.importdat(fp.FilePath)
            fp.Numpoints = self.prof.Numpoints
            fp.Thickness = max(self.prof.Thickness[:, 1]) * 1000.
            #fp.Camber = max(self.prof.Camber[:, 1]) *1000.
            fp.coords = map(
                lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Thickness":
            self.prof.Thickness = fp.Thickness / 1000.
            fp.coords = map(
                lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        elif prop == "Numpoints":
        #     self.prof.Numpoints = fp.Numpoints
        #     fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
        # elif prop == "Camber":
        #     self.prof.Camber = fp.Camber /1000.
        #     fp.coords = map(lambda x: FreeCAD.Vector(x[0], x[1], 0.), self.prof.Profile)
            pass


class ViewProviderAirfoil():

    def __init__(self, obj):
        obj.addProperty(
            "App::PropertyLength", "LineWidth", "Base", "Line width")
        obj.addProperty(
            "App::PropertyColor", "LineColor", "Base", "Line color")
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

    def updateData(self, fp, prop):
        'jkhjkn'
        if prop == "coords":
            points = fp.getPropertyByName("coords")
            self.data.point.setValue(0, 0, 0)
            self.data.point.setValues(0, len(points), points)
            nums = range(len(points))
            self.lineset.coordIndex.setValue(0)
            self.lineset.coordIndex.setValues(0, len(nums), nums)
        pass

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
        "Return a list of display modes."
        modes = []
        modes.append("Shaded")
        return modes
        pass


class moveablePoint():

    """FreeCAD Point"""

    def __init__(self, obj, x, y):

        obj.addProperty("App::PropertyFloat", "x", "coor", "cor-x").x = x
        obj.addProperty("App::PropertyFloat", "y", "coor", "cor-y").y = y
        obj.Proxy = self

    def execute(self, fp):
        pass

    def onChanged(self, fp, prop):
        pass


class ViewProvidermoveablePoint():

    def __init__(self, obj, lineobject):
        self.lineobject = lineobject
        self.object = obj.Object
        self.highlightind = False
        self.drag = False
        self.view = FreeCADGui.ActiveDocument.ActiveView
        self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.highlight_cb)
        self.view.addEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.begin_drag_cb)
        obj.Proxy = self

    def attach(self, vobj):
        self.out = coin.SoSeparator()
        self.point = coin.SoPointSet()
        self.data = coin.SoCoordinate3()
        self.drawstyle = coin.SoDrawStyle()
        self.color = coin.SoMaterial()
        self.color.diffuseColor.setValue(0, 0, 0)
        self.drawstyle.style = coin.SoDrawStyle.POINTS
        self.drawstyle.pointSize = 5.
        self.out.addChild(self.color)
        self.out.addChild(self.drawstyle)
        self.out.addChild(self.data)
        self.out.addChild(self.point)
        vobj.addDisplayMode(self.out, 'out')

    def updateData(self, fp, prop):
        if prop in ["x", "y"]:
            self.x = fp.x
            self.y = fp.y
            self.data.point.setValue(self.x, self.y, 0)
            self.lineobject.Object.ischanged = False

    def getDisplayModes(self, obj):
        "Return a list of display modes."
        modes = []
        modes.append("out")
        return modes
        pass

    def highlight_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        #FreeCAD.Console.PrintWarning(str(pos)+"bla")
        s = self.view.getPointOnScreen(self.x, self.y, 0.)
        if (abs(s[0] - pos[0]) ** 2 +  abs(s[1] - pos[1]) ** 2) < (15 ** 2):
            if self.highlightind:
                pass
            else:
                self.drawstyle.pointSize = 10.
                self.color.diffuseColor.setValue(0, 1, 1)
                self.highlightind = True
        else:
            if self.highlightind:
                self.drawstyle.pointSize = 5.
                self.highlightind = False
                self.color.diffuseColor.setValue(0, 0, 0)

    def begin_drag_cb(self, cb):
        event = cb.getEvent()
        if self.highlightind and event.getState() == coin.SoMouseButtonEvent.DOWN:
            if self.drag == 0:
                self.dragcb = self.view.addEventCallbackPivy(
                    coin.SoLocation2Event.getClassTypeId(), self.drag_cb)
                self.drag = 1
            elif self.drag == 1:
                self.view.removeEventCallbackPivy(
                    coin.SoLocation2Event.getClassTypeId(), self.dragcb)
                self.drag = 0

    def drag_cb(self, cb):
        event = cb.getEvent()
        pos = event.getPosition()
        point = self.view.getPoint(pos[0], pos[1])
        self.object.x = point[0]
        self.object.y = point[1]
        self.data.point.setValue(self.x, self.y, 0)

class moveableLine():

    """FreeCAD Point"""

    def __init__(self, obj, points):
        obj.addProperty("App::PropertyLinkList", "points", "test", "test")
        obj.addProperty("App::PropertyBool", "ischanged", "test", "test")

        obj.points = points
        obj.ischanged = True
        obj.Proxy = self
        self.Object = obj

    def execute(self, fp):
        pass

    def onChanged(self, fp, prop):
        pass

    def addObject(self, child):
        temp = self.Object.points
        temp.append(child)
        self.Object.points = temp

    def insertObject(self, pos, child):
        temp = self.Object.points
        temp.insert(pos, child)
        self.Object.points = temp


class ViewProvidermoveableLine():

    def __init__(self, obj):
        self.object = obj.Object
        obj.Proxy = self

    def claimChildren(self):
        return(self.object.points)

    def attach(self, vobj):
        self.seperator = coin.SoSeparator()
        self.point = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor.setValue(0, 0, 0)
        self.seperator.addChild(self.color)
        self.seperator.addChild(self.data)
        self.seperator.addChild(self.point)
        vobj.addDisplayMode(self.seperator, 'out')

    def updateData(self, fp, prop):
        p = [[i.x, i.y, 0] for i in fp.points]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)

    def getDisplayModes(self, obj):
        "Return a list of display modes."
        modes = []
        modes.append("out")
        return modes


from openglider.Utils import Bezier

class moveableSpline():

    """FreeCAD Point"""

    def __init__(self, obj, points):
        obj.addProperty("App::PropertyLinkList", "points", "test", "test")
        obj.addProperty("App::PropertyBool", "ischanged", "test", "test")

        obj.points = points
        obj.ischanged = True
        obj.Proxy = self
        self.Object = obj

    def execute(self, fp):
        pass

    def onChanged(self, fp, prop):
        pass

    def addObject(self, child):
        temp = self.Object.points
        temp.append(child)
        self.Object.points = temp

    def insertObject(self, pos, child):
        temp = self.Object.points
        temp.insert(pos, child)
        self.Object.points = temp



#class moveableSpline(moveableLine):
#    pass

# class ViewProvidermoveableSpline(ViewProvidermoveableLine):
#     def __init__(self, obj):
#         ViewProvidermoveableLine.__init__(self,obj)
#         self.bezier = Bezier.BezierCurve([[0,0],[1,0]])

#     def updateData(self, fp, prop):
#         num = 100
#         data = [self.bezier(i*1./(num-1)) for i in range(num)]
#         self.data.point.setValue(0, 0, 0)
#         self.data.point.setValues(0, len(data), data)



class ViewProvidermoveableSpline():

    def __init__(self, obj):
        self.object = obj.Object
        self.bezier = Bezier.BezierCurve([[0,1],[2,3],[3,0]])
        obj.Proxy = self

    def claimChildren(self):
        return(self.object.points)

    def attach(self, vobj):
        self.seperator = coin.SoSeparator()
        self.point = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor.setValue(0, 0, 0)
        self.seperator.addChild(self.color)
        self.seperator.addChild(self.data)
        self.seperator.addChild(self.point)
        vobj.addDisplayMode(self.seperator, 'out')

    def updateData(self, fp, prop):
        num = 20
        self.bezier.ControlPoints = [[i.x, i.y] for i in self.object.points]
        data = [self.bezier(i*1./(num-1)).tolist() + [0] for i in range(num)]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(data), data)

    def getDisplayModes(self, obj):
        "Return a list of display modes."
        modes = []
        modes.append("out")
        return modes