from pivy import coin
import FreeCADGui as gui


class ControlPoint(coin.SoSeparator):
    def __init__(self, x=0, y=0, z=0):
        super(ControlPoint, self).__init__()
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

    def set_pos(self, new_pos):
        self.x = new_pos[0]
        self.y = new_pos[1]
        self.z = new_pos[2]
        self.coordinate.point.setValue(self.x, self.y, self.z)

    def set_edit_mode(self):
        self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_7_7

    def unset_edit_mode(self):
        self.marker.markerIndex = coin.SoMarkerSet.CROSS_5_5

    def set_mouse_over(self):
        self.mouse_over = True
        self.mat.diffuseColor.setValue(1, 1, 0)

    def unset_mouse_over(self):
        self.mouse_over = False
        self.mat.diffuseColor.setValue(0, 0, 0)


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
        self.trigger_func = None
        self.is_edit = False

    def set_edit_mode(self, view, triggerfunc=None):
        print(self.is_edit)
        if not self.is_edit:
            self.is_edit = True
            self.view = view
            self.trigger_func = triggerfunc
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
        print(event.getKey())
        if event.getKey() == 65307:
            self.unset_edit_mode()


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
                        self.current_point = point
                        if not point.mouse_over:
                            point.set_mouse_over()
                    else:
                        if point.mouse_over:
                            point.unset_mouse_over()

    #---------INITDRAG---------------------#
    def drag_main_cb(self, event_callback):
        event = event_callback.getEvent()
        if self.current_point is not None and not self.drag_check:
            self.drag_check = True
            self.drag = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.drag_cb)
        elif self.drag is not None and self.drag_check:
            self.drag_check = False
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.drag)
            self.drag = None

    def drag_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        if type(event) == coin.SoLocation2Event:
            self.current_point.set_pos(self.view.getPoint(pos[0], pos[1]))
            self.trigger_func()

    def add_point(self):
        pass

    def sort(self):
        pass

    def remove_point(self):
        pass


class Line():
    """FreeCAD Point"""
    def __init__(self, obj, points):
        obj.addProperty("App::PropertyVectorList", "points", "points", "points")
        obj.points = points
        obj.Proxy = self

    def execute(self, fp):
        pass

    def onChanged(self, fp, prop):
        pass

class VpLine():
    def __init__(self, obj):
        self.obj = obj.Object
        self.point_container = ControlPointContainer(self.obj.points)
        obj.Proxy = self

    def attach(self, vobj):
        print("abc")
        self.seperator = coin.SoSeparator()
        self.point = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor.setValue(0, 0, 0)
        self.seperator.addChild(self.point_container)
        self.seperator.addChild(self.color)
        self.seperator.addChild(self.data)
        self.seperator.addChild(self.point)
        vobj.addDisplayMode(self.seperator, 'out')

    def updateData(self, fp=None, prop=None):
        p = [[i.x, i.y, i.z] for i in self.point_container.control_points]
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(p), p)

    def getDisplayModes(self, obj):
        modes = []
        modes.append("out")
        return modes

    def doubleClicked(self, vobj):
        self.point_container.set_edit_mode(gui.ActiveDocument.ActiveView, self.updateData)
