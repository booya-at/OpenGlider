import numpy as np

from pivy import coin
import FreeCAD as App
from openglider.vector.spline import Bezier


COLORS ={
    'black': (0, 0, 0),
    'white': (1., 1., 1.),
    'grey': (0.5, 0.5, 0.5),
    'red': (1., 0., 0.),
    'blue': (0., 0., 1.),
    'green': (0., 1., 1.),
    'yellow': (0., 1., 0.)
}

COL_STD = COLORS['black']
COL_OVR = COLORS['red']
COL_SEL = COLORS['yellow']


class ControlPoint(coin.SoSeparator):
    lock = False
    def __init__(self, x=0, y=0, z=0):
        super(ControlPoint, self).__init__()
        self.marker = coin.SoMarkerSet()
        self.mat = coin.SoMaterial()
        self.coordinate = coin.SoCoordinate3()
        self.setup_coin(x, y, z)
        self.fix = False

    def setup_coin(self, x, y, z):
        self.mat.setName('mat')
        self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9
        self.mat.diffuseColor.setValue(*COL_STD)
        self += [self.coordinate, self.mat, self.marker]
        self.pos = [float(x), float(y), float(z)]

    @property
    def pos(self):
        return [i for i in self.coordinate.point.getValues()[0].getValue()]

    @pos.setter
    def pos(self, new_pos):
        pos = self.constraint(new_pos)
        self.coordinate.point.setValue(pos[0], pos[1], pos[2] or 0.)

    def set_x(self, new_x):
        pos = self.pos
        pos[0] = self.constraint([new_x, 0., 0.])[0]
        self.coordinate.point.setValue(*pos)

    def set_y(self, new_y):
        pos = self.pos
        pos[1] = self.constraint([0., new_y, 0.])[1]
        self.coordinate.point.setValue(*pos)

    def set_z(self, new_z):
        pos = self.pos
        pos[2] = self.constraint([0., 0., new_z])[2]
        self.coordinate.point.setValue(*pos)

    def set_edit(self):
        if not ControlPoint.lock:
            ControlPoint.lock = True
            self.mat.diffuseColor.setValue(*COL_SEL)

    def unset_edit(self):
        ControlPoint.lock = False
        self.mat.diffuseColor.setValue(*COL_STD)

    @property
    def is_edit(self):
        return self.mat.diffuseColor == COL_SEL

    def constraint(self, new_pos):
        'overwrite for special behavior'
        return new_pos


class ControlPointContainer(coin.SoSeparator):
    def __init__(self, points=None, view=None):
        super(ControlPointContainer, self).__init__()
        self.control_points = []
        if points is not None:
            for point in points:
                cp = ControlPoint(*point)
                self.control_points.append(cp)
                self += [cp]
        self.view = view
        self._current_point = None
        self.drag = None
        self.old_mouse_pos = None
        self.new_mouse_pos = None
        self.on_drag = []
        self.drag_start = []
        self.drag_release = []
        self.grid = [0.1, 0.1, 100]
        self.highlite_main = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.highlight_cb)
        self.drag_main = self.view.addEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.drag_main_cb)

    @property
    def control_pos(self):
        return [i.pos for i in self.control_points]

    @control_pos.setter
    def control_pos(self, points):
        self.control_points = [ControlPoint(*point) for point in points]
        self.removeAllChildren()
        self += self.control_points

    @property
    def current_point(self):
        return self._current_point

    @current_point.setter
    def current_point(self, cp):
        if cp != self._current_point:
            if self.current_point is not None:
                self._current_point.unset_edit()
            self._current_point = cp
            if self._current_point is not None:
                self._current_point.set_edit()

    def highlight_cb(self, event_callback):
        if not ControlPoint.lock or self.current_point is not None:
            event = event_callback.getEvent()
            pos = event.getPosition()
            render_manager = self.view.getViewer().getSoRenderManager()
            ray_pick = coin.SoRayPickAction(render_manager.getViewportRegion())
            ray_pick.setPoint(coin.SbVec2s(*pos))
            ray_pick.setRadius(10)
            ray_pick.setPickAll(True) 
            ray_pick.apply(render_manager.getSceneGraph())
            picked_point = ray_pick.getPickedPointList()
            for point in picked_point:
                path = point.getPath()
                length = path.getLength()
                point = path.getNode(length - 2)
                point = list(filter(lambda ctrl: ctrl.getNodeId() == point.getNodeId(), self.control_points))
                if point != []:
                    if (not hasattr(point[0], 'fix') or not point[0].fix):
                        self.current_point = point[0]
                        break
            else:
                self.current_point = None

        #---------INITDRAG---------------------#
    def drag_main_cb(self, event_callback):
        event = event_callback.getEvent()
        if self.current_point is not None and event.getState():
            pos = event.getPosition()
            self.old_mouse_pos = self.view.getPoint(*pos)
            self.drag = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.drag_cb) 
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.highlite_main)
            for foo in self.drag_start:
                foo()
        elif self.drag is not None:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.drag)
            self.highlite_main = self.view.addEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.highlight_cb)
            self.drag = None
            for foo in self.drag_release:
                foo()

    def drag_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        if type(event) == coin.SoLocation2Event and self.current_point:
            if not self.current_point.fix:
                self.new_mouse_pos = self.view.getPoint(*pos)
                if event.wasCtrlDown():
                    scaled_pos = [(i-j)* 0.2 + k for i, j, k in zip(self.new_mouse_pos, self.old_mouse_pos, self.current_point.pos)]
                elif event.wasShiftDown():
                    scaled_pos = [round(pos/self.grid[i]) * self.grid[i] for i, pos in enumerate(self.new_mouse_pos)]
                else:
                    scaled_pos = self.new_mouse_pos
                self.current_point.pos = scaled_pos
                self.old_mouse_pos = self.new_mouse_pos
                for foo in self.on_drag:
                    foo()

    def remove_callbacks(self):
        if self.highlite_main:
            self.view.removeEventCallbackPivy(coin.SoLocation2Event.getClassTypeId(), self.highlite_main)
        if self.drag_main:
            self.view.removeEventCallbackPivy(coin.SoMouseButtonEvent.getClassTypeId(), self.drag_main)


class Line(object):
    def __init__(self, points, color='black', width=1):
        self.object = coin.SoSeparator()
        self.ls = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.drawstyle = coin.SoDrawStyle()
        self.points = list(map(vector3D, points))
        self.color.diffuseColor = COLORS[color]
        self.drawstyle.lineWidth = width
        self.update()
        self.object += [self.color, self.drawstyle, self.data, self.ls]

    def update(self, points=None):
        if points is not None:
            self.points = list(map(vector3D, points))
        self.data.point.deleteValues(0)
        self.data.point.setValues(0, len(self.points), self.points)

    @property
    def pos(self):
        return self.data.point.values

    @pos.setter
    def pos(self, value):
        self.update(value)

class Line1(coin.SoSeparator):
    def __init__(self, points, color='black'):
        self.ls = coin.SoLineSet()
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.points = list(map(vector3D, points))
        self.color.diffuseColor = COLORS[color]
        self.update()
        self += [self.color, self.data, self.ls]

    def update(self, points=None):
        if points is not None:
            self.points = list(map(vector3D, points))
        self.data.point = coin.deleteValues(0)
        self.data.point.setValues(0, len(self.points), self.points)

    def set_color(self, color):
        self.color.diffuseColor = COLORS[color]


class Marker(coin.SoSeparator):
    def __init__(self, points=[], color='black'):
        super(Marker, self).__init__()
        self.marker = coin.SoMarkerSet()
        self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor = COLORS[color]
        self.update(points)
        self += [self.color, self.data, self.marker]

    def update(self, points=None):
        if points is not None:
            self.points = list(map(vector3D, points))
        self.data.point = coin.deleteValues(0)
        self.data.point.setValues(0, len(self.points), self.points)

    def set_color(self, color):
        self.color.diffuseColor = COLORS[color]

    @property
    def pos(self):
        return self.data.point.values

    @pos.setter
    def pos(self, value):
        self.update(value)

class Arrow(Line):
    def __init__(self, points, color="black", arrow_size=0.04, length=2):
        super(Arrow, self).__init__(points, color)
        self.arrow_sep = coin.SoSeparator()
        self.arrow_rot = coin.SoRotation()
        self.arrow_scale = coin.SoScale()
        self.arrow_translate = coin.SoTranslation()
        self.arrow_scale.scaleFactor = (arrow_size, arrow_size, arrow_size)
        self.cone = coin.SoCone()
        arrow_length = coin.SoScale()
        arrow_length.scaleFactor = (1, length, 1)
        arrow_origin = coin.SoTranslation()
        arrow_origin.translation = (0, -1, 0)
        self.arrow_sep += [self.arrow_translate, self.arrow_rot, self.arrow_scale]
        self.arrow_sep += [arrow_length, arrow_origin, self.cone]
        self.object += [self.arrow_sep]
        self.set_arrow_direction()

    def set_arrow_direction(self):
        pts = np.array(self.pos)
        self.arrow_translate.translation = tuple(pts[-1])
        direction = pts[-1] - pts[-2]
        direction /= np.linalg.norm(direction)
        _rot = coin.SbRotation()
        _rot.setValue(coin.SbVec3f(0, 1, 0), coin.SbVec3f(*direction))
        self.arrow_rot.rotation.setValue(_rot)


class Spline(Line):
    def __init__(self, control_points, num=50):
        self.bezier_curve = Bezier(controlpoints=control_points)
        self.num = num
        points = self.bezier_curve.get_sequence(num)
        super(Spline, self).__init__(points)

    # def update(self, points=None):
    #     if points is not None:
    #         self.bezier_curve.controlpoints = vector3D(points)
    #     super(Spline, self).update(points=[self.bezier_curve(i * 1. / (self.num - 1)) for i in range(self.num)])


def vector3D(vec):
    if len(vec) == 2:
        return list(vec) + [0.]
    else:
        return vec

def vector2D(vec):
    return vec[0:2]
