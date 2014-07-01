from _base import OGBaseObject, OGBaseVP, OGSpline, OGSplineVP


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