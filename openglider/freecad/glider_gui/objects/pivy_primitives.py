from pivy import coin
from openglider.utils.bezier import BezierCurve
import numpy

color_dict ={
    "black": (0, 0, 0),
    "white": (1., 1., 1.),
    "gray": (0.5, 0.5, 0.5)
}

def None_func():
    pass

#-------------------------BEGIN-BASE-Object-----------------------#
class ControlPoint(coin.SoSeparator):
    lock = None
    def __init__(self, x=0, y=0, z=0):
        super(ControlPoint, self).__init__()
        self.x = 0.
        self.y = 0.
        self.z = 0.
        self.marker = coin.SoMarkerSet()
        self.marker.markerIndex = coin.SoMarkerSet.CROSS_5_5
        self.mat = coin.SoMaterial()
        self.mat.diffuseColor.setValue(0., 0., 0.)
        self.coordinate = coin.SoCoordinate3()
        self.set_pos([x, y, z])
        self.switch = coin.SoSwitch()
        self.addChild(self.coordinate)
        self.addChild(self.switch)
        self.addChild(self.mat)
        self.addChild(self.marker)

        self.mouse_over = False
        self.fix = False

    def set_x(self, new_x):
        self.x = self.constraint([new_x, 0., 0.])[0]
        self.coordinate.point.setValue(self.x, self.y, self.z)

    def set_y(self, new_y):
        self.y = self.constraint([0., new_y, 0.])[1]
        self.coordinate.point.setValue(self.x, self.y, self.z)

    def set_z(self, new_z):
        self.z = self.constraint([0., 0., new_z])[2]
        self.coordinate.point.setValue(self.x, self.y, self.z)

    def set_pos(self, new_pos):
        self.x, self.y, self.z = self.constraint(new_pos)
        self.coordinate.point.setValue(self.x, self.y, self.z)

    def set_edit_mode(self):
        if not self.fix:
            self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9

    def unset_edit_mode(self):
        self.marker.markerIndex = coin.SoMarkerSet.CROSS_5_5

    def set_mouse_over(self):
        if not ControlPoint.lock:
            self.mouse_over = True
            self.mat.diffuseColor.setValue(1, 1, 0)
            ControlPoint.lock = True

    def unset_mouse_over(self):
        self.mouse_over = False
        self.mat.diffuseColor.setValue(0, 0, 0)
        ControlPoint.lock = False

    def constraint(self, pos):
        "overwrite for special behavior"
        return [pos[0], pos[1], 0.]


class ControlPointContainer(coin.SoSeparator):
    def __init__(self, points=None):
        super(ControlPointContainer, self).__init__()
        self.control_points = [ControlPoint(*point) for point in points]
        for cp in self.control_points:
            self.addChild(cp)

        self.view = None
        self.highlite_main = None
        self.drag = None
        self.drag_check = False
        self.current_point = None
        self.on_drag = []
        self.drag_start = []
        self.drag_release = []
        self.is_edit = False

    @property
    def control_point_list(self):
        return [[i.x, i.y, i.z] for i in self.control_points]

    def set_edit_mode(self, view):
        if not self.is_edit:
            self.is_edit = True
            self.view = view
            for pt in self.control_points:
                pt.set_edit_mode()
            self.highlite_main = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.highlight_cb)
            self.drag_main = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.drag_main_cb)
            self.exit = self.view.addEventCallbackPivy(coin.SoKeyboardEvent.getClassTypeId(), self.exit_cb)
        else:
            self.unset_edit_mode()


    def unset_edit_mode(self):
        if self.is_edit:
            self.is_edit = False
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.highlite_main)
            self.view.removeEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.drag_main)
            self.view.removeEventCallbackPivy(coin.SoKeyboardEvent.getClassTypeId(), self.exit)
            for pt in self.control_points:
                pt.unset_edit_mode()
            self.view = None

    def exit_cb(self, event_callback):
        event = event_callback.getEvent()
        if event.getKey() == 65307:
            self.unset_edit_mode()

    def set_control_points(self, points):
        self.control_points = [ControlPoint(*point) for point in points]
        self.removeAllChildren()
        for i in self.control_points:
            if self.is_edit:
                i.set_edit_mode()
            self.addChild(i)


    def highlight_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        #-------------HIGHLIGHT----------------#
        if not self.drag:
            if type(event) == coin.SoLocation2Event:
                self.current_point = None
                for point in self.control_points:
                    s = self.view.getPointOnScreen(point.x, point.y, point.z)
                    if (abs(s[0] - pos[0]) ** 2 + abs(s[1] - pos[1]) ** 2) < (15 ** 2):
                        if not point.mouse_over:
                            point.set_mouse_over()
                        if point.mouse_over and not point.fix:
                            self.current_point = point
                    else:
                        if point.mouse_over:
                            point.unset_mouse_over()

    #---------INITDRAG---------------------#
    def drag_main_cb(self, event_callback):
        event = event_callback.getEvent()
        if self.current_point is not None and not self.drag_check and event.getState():
            self.drag_check = True
            self.drag = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.drag_cb)
            for foo in self.drag_start:
                foo()
        elif self.drag is not None and self.drag_check:
            self.drag_check = False
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.drag)
            self.drag = None
            for foo in self.drag_release:
                foo()

    def drag_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        if type(event) == coin.SoLocation2Event:
            self.current_point.set_pos(self.view.getPoint(pos[0], pos[1]))
            for foo in self.on_drag:
                foo()

    def add_point(self):
        pass

    def sort(self):
        pass

    def remove_point(self):
        pass




class Line(object):
    def __init__(self, points, color="black"):
        self.object = coin.SoSeparator()
        self.ls = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.points = vector3D(points)
        self.color.diffuseColor = color_dict[color]
        self.update()
        self.object.addChild(self.color)
        self.object.addChild(self.data)
        self.object.addChild(self.ls)

    def update(self, points=None):
        if points is not None:
            self.points = vector3D(points)
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(self.points), self.points)


class Spline(Line):
    def __init__(self, control_points, num=50):
        self.bezier_curve = BezierCurve(controlpoints=control_points)
        self.num_points = num
        super(Spline, self).__init__(self.bezier_curve.get_sequence(num))

    def update(self, points=None):
        if points is not None:
            self.bezier_curve.controlpoints = vector3D(points)
        super(Spline, self).update(points=[self.bezier_curve(i * 1. / (self.num - 1)) for i in range(self.num)])

    @property
    def num(self):
        return self.num_points

    @num.setter
    def num(self, num):
        self.numpoints = num
        self.update(self.bezier_curve.controlpoints)


def vector3D(vec):
    if not isinstance(vec[0], (list, tuple, numpy.ndarray)):
        if len(vec) == 3:
            return vec
        elif len(vec) == 2:
            return numpy.array(vec).tolist() + [0.]
        else:
            print("something wrong with this list: ", vec)
    else:
        return [vector3D(i) for i in vec]


if __name__ == "__main__":
    print(vector3D([[0, 1], [2, 3]]))



