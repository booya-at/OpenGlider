from _base import ControlPointContainer


class OGBaseObject(object):
    def __init__(self, obj):
        obj.Proxy = self

    def execute(self, fp):
        pass


class OGBaseVP(object):
    def __init__(self, obj):
        obj.Proxy = self

    def attach(self, vobj):
        pass

    def updateData(self, fp, prop):
        pass

    def getDisplayModes(self, obj):
        mod = ["out"]
        return(mod)


class OGBaseControlObject(OGBaseObject):
    def __init__(self, obj, points):
        obj.addProperty("App::PropertyVectorList", "points", "points", "points")
        obj.points = points
        super(OGBaseControlObject, self).__init__(obj)


class OGBaseControlVP(OGBaseVP):
    def __init__(self, obj):
        self.obj = obj.Object
        self.point_container = ControlPointContainer(self.obj.points)
        self.separator = None
        super(OGBaseControlVP, self).__init__(obj)


    def attach(self, vobj):
        self.separator = coin.SoSeparator()
        self.separator.addChild(self.point_container)
        self.add_to_view()
        vobj.addDisplayMode(self.separator, 'out')

    def add_to_view(self):
        """overwrite add childs to self.separator"""

    def _updateData(self):
        self.updateData(fp=None, prop=None)

    def doubleClicked(self, vobj):
        self.point_container.set_edit_mode(gui.ActiveDocument.ActiveView, self._updateData)
#----------------------------------END-BASE-Object----------------------#


#------------------------------OBJECT-----------------------#
class OGLine(OGBaseControlObject):
    def __init__(self, obj, points):
        super(OGLine, self).__init__(obj, points)


class OGSpline(OGBaseControlObject):
    def __init__(self, obj, points):
        super(OGSpline, self).__init__(obj, points)


#-----------------------------VIEWPROVIDER------------------#
class OGLineVP(OGBaseControlVP):
    def __init__(self, obj):
        super(OGLineVP, self).__init__(obj)

    def add_to_view(self):
        self.point = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor.setValue(0, 0, 0)
        self.separator.addChild(self.color)
        self.separator.addChild(self.data)
        self.separator.addChild(self.point)

    def updateData(self, fp, prop):
        p = [[i.x, i.y, i.z] for i in self.point_container.control_points]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)


class OGSplineVP(OGBaseControlVP):
    def __init__(self, obj):
        self.bezier_curve = BezierCurve()
        self.num = 10
        obj.addProperty("App::PropertyInteger", "num", "num", "num").num = self.num
        super(OGSplineVP, self).__init__(obj)

    def add_to_view(self):
        self.point = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor.setValue(0, 0, 0)
        self.separator.addChild(self.color)
        self.separator.addChild(self.data)
        self.separator.addChild(self.point)

    def onChanged(self, fp, prop):
        if prop == "num":
            self.num = fp.num
            self.updateData(None, None)

    def updateData(self, fp, prop):
        self.bezier_curve.controlpoints = self.point_container.control_point_list
        p = [self.bezier_curve(i * 1. / (self.num - 1)) for i in range(self.num)]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)


class OGSymSplineVP(OGSplineVP):
    def updateData(self, fp, prop):
        temp = self.point_container.control_point_list
        self.bezier_curve.controlpoints = [[-i[0], i[1], i[2]]for i in temp[::-1]] + temp
        p = [self.bezier_curve(i * 1. / (self.num - 1)) for i in range(self.num)]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)


class OGShape(OGBaseObject):
    def __init__(self, obj, upperspline, lowerspline):
        obj.addProperty("App::PropertyLink", "upper_spline", "upper_spline", "upper_spline")
        obj.addProperty("App::PropertyLink", "lower_spline", "lower_spline", "lower_spline")
        obj.upper_spline = upperspline
        obj.lower_spline = lowerspline
        super(OGShape, self).__init__(obj)

class OGShapeVP(OGBaseVP):
    def __init__(self, obj):
        self.obj = obj.Object
        super(OGShapeVP, self).__init__(obj)

    def attach(self, vobj):
        pass

    def updateData(self, fp, prop):
        pass


    def claimChildren(self):
        return [self.obj.upper_spline, self.obj.lower_spline]