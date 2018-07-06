from pivy import coin
import FreeCAD as App
import numpy as np

def depth(l):
    return isinstance(l, (list, tuple, np.ndarray)) and max(map(depth, l)) + 1


def vector3D(vec):
    if len(vec) == 0:
        return(vec)
    elif not isinstance(vec[0], (list, tuple, np.ndarray, App.Vector)):
        if len(vec) == 3:
            return vec
        elif len(vec) == 2:
            return np.array(vec).tolist() + [0.]
        else:
            print('something wrong with this list: ', vec)
    else:
        return [vector3D(i) for i in vec]


COLORS = {
    'black': (0, 0, 0),
    'white': (1., 1., 1.),
    'grey': (0.5, 0.5, 0.5),
    'red': (1., 0., 0.),
    'blue': (0., 0., 1.),
    'green': (0., 1., 1.),
    'yellow': (0., 1., 0.)
}


class Object3D(coin.SoSeparator):
    std_col = 'black'
    ovr_col = 'red'
    sel_col = 'yellow'
    disabled_col = 'grey'

    def __init__(self, points, dynamic=False):
        super(Object3D, self).__init__()
        self._sel_color = COLORS[self.sel_col]
        self._ovr_color = COLORS[self.ovr_col]
        self._std_color = COLORS[self.std_col]
        self.data = coin.SoCoordinate3()
        self.color = coin.SoMaterial()
        self.color.diffuseColor = self._std_color
        self.addChild(self.color)
        self.addChild(self.data)
        self.start_pos = None
        self.dynamic = dynamic
        self.on_drag = []
        self.on_drag_release = []
        self.on_drag_start = []
        self._delete = False
        self._tmp_points = None
        self.enabled = True
        if depth(points) != 2:
            raise AttributeError('depth of list should be 2')
        self.points = points

    def set_disabled(self):
        try:
            self.color.diffuseColor = COLORS[self.disabled_col]
        except KeyError:
            self.color.diffuseColor = self.disabled_col
        self.enabled = False

    def set_enabled(self):
        try:
            self.color.diffuseColor = COLORS[self.std_col]
        except KeyError:
            self.color.diffuseColor = self.std_col
        self.enabled = True

    def set_color(self, col):
        self.std_col = col
        try:
            self._std_color = COLORS[self.std_col]
            self.color.diffuseColor = self._std_color
        except KeyError:
            self._std_color = self.std_col
            self.color.diffuseColor = self._std_color


    @property
    def points(self):
        return self.data.point.getValues()

    @points.setter
    def points(self, points):
        self.data.point.setValue(0, 0, 0)
        self.data.point.setValues(0, len(points), points)

    def set_mouse_over(self):
        if self.enabled:
            self.color.diffuseColor = self._ovr_color

    def unset_mouse_over(self):
        if self.enabled:
            self.color.diffuseColor = self._std_color

    def select(self):
        if self.enabled:
            self.color.diffuseColor = self._sel_color

    def unselect(self):
        if self.enabled:
            self.color.diffuseColor = self._std_color

    def drag(self, mouse_coords, fact=1.):
        if self.enabled:
            pts = self.points
            for i, pt in enumerate(pts):
                pt[0] = mouse_coords[0] * fact + self._tmp_points[i][0]
                pt[1] = mouse_coords[1] * fact + self._tmp_points[i][1]
                pt[2] = mouse_coords[2] * fact + self._tmp_points[i][2]
            self.points = pts
            for i in self.on_drag:
                i()

    def drag_release(self):
        if self.enabled:
            for i in self.on_drag_release:
                i()

    def drag_start(self):
        self._tmp_points = self.points
        if self.enabled:
            for i in self.on_drag_start:
                i()

    @property
    def drag_objects(self):
        if self.enabled:
            return [self]

    def delete(self):
        if self.enabled and not self._delete:
            self.removeAllChildren()
            self._delete = True

    def check_dependency(self):
        pass


class Marker(Object3D):
    def __init__(self, points, dynamic=False):
        super(Marker, self).__init__(points, dynamic)
        self.marker = coin.SoMarkerSet()
        self.marker.markerIndex = coin.SoMarkerSet.CIRCLE_FILLED_9_9
        self.addChild(self.marker)


class Line(Object3D):
    def __init__(self, points, dynamic=False):
        super(Line, self).__init__(points, dynamic)
        self.drawstyle = coin.SoDrawStyle()
        self.line = coin.SoLineSet()
        self.addChild(self.drawstyle)
        self.addChild(self.line)

class Polygon(Object3D):
    def __init__(self, points, dynamic=False):
        super(Polygon, self).__init__(points, dynamic)
        self.polygon = coin.SoFaceSet()
        self.addChild(self.polygon)

class Arrow(Line):
    def __init__(self, points, dynamic=False, arrow_size=0.04, length=2):
        super(Arrow, self).__init__(points, dynamic)
        self.arrow_sep = coin.SoSeparator()
        self.arrow_rot = coin.SoRotation()
        self.arrow_scale = coin.SoScale()
        self.arrow_translate = coin.SoTranslation()
        self.arrow_scale.scaleFactor.setValue(arrow_size, arrow_size, arrow_size)
        self.cone = coin.SoCone()
        arrow_length = coin.SoScale()
        arrow_length.scaleFactor = (1, length, 1)
        arrow_origin = coin.SoTranslation()
        arrow_origin.translation = (0, -1, 0)
        self.arrow_sep += [self.arrow_translate, self.arrow_rot, self.arrow_scale]
        self.arrow_sep += [arrow_length, arrow_origin, self.cone]
        self += [self.arrow_sep]
        self.set_arrow_direction()

    def set_arrow_direction(self):
        pts = np.array(self.points)
        self.arrow_translate.translation = tuple(pts[-1])
        direction = pts[-1] - pts[-2]
        direction /= np.linalg.norm(direction)
        _rot = coin.SbRotation()
        _rot.setValue(coin.SbVec3f(0, 1, 0), coin.SbVec3f(*direction))
        self.arrow_rot.rotation.setValue(_rot)



class InteractionSeparator(coin.SoSeparator):
    def __init__(self):
        super(InteractionSeparator, self).__init__()
        self.objects = []
        self.static_objects = []
        self.selected_objects = []
        self.drag_objects = []
        self.over_object = None
        self.start_pos = None
        self.view = None
        self.on_drag = []
        self.on_drag_release = []
        self.on_drag_start = []
        self._direction = None

    def addChild(self, child):
        super(InteractionSeparator, self).addChild(child)
        if hasattr(child, 'dynamic'):
            if child.dynamic:
                self.objects.append(child)
            else:
                self.static_objects.append(child)

    def addChildren(self, children):
        for i in children:
            self.addChild(i)

    def Highlight(self, obj):
        if self.over_object:
            self.over_object.unset_mouse_over()
        self.over_object = obj
        if self.over_object:
            self.over_object.set_mouse_over()
        self.ColorSelected()

    def Select(self, obj, multi=False):
        if not multi:
            for o in self.selected_objects:
                o.unselect()
            self.selected_objects = []
        if obj:
            if obj in self.selected_objects:
                self.selected_objects.remove(obj)
            else:
                self.selected_objects.append(obj)
        self.ColorSelected()
        self.selection_changed()

    def selection_changed(self):
        pass

    def ColorSelected(self):
        for obj in self.selected_objects:
            obj.select()

    def cursor_pos(self, event):
        pos = event.getPosition()
        return self.view.getPoint(*pos)

    def mouse_over_cb(self, event_callback):
        event = event_callback.getEvent()
        pos = event.getPosition()
        obj = self.SendRay(pos)
        self.Highlight(obj)

    def SendRay(self, mouse_pos):
        '''sends a ray trough the scene and return the nearest entity'''
        render_manager = self.view.getViewer().getSoRenderManager()
        ray_pick = coin.SoRayPickAction(render_manager.getViewportRegion())
        ray_pick.setPoint(coin.SbVec2s(*mouse_pos))
        ray_pick.setRadius(10)
        ray_pick.setPickAll(True)
        ray_pick.apply(render_manager.getSceneGraph())
        picked_point = ray_pick.getPickedPointList()
        return self.ObjById(picked_point)

    def ObjById(self, picked_point):
        for point in picked_point:
            path = point.getPath()
            length = path.getLength()
            point = path.getNode(length - 2)
            point = list(filter(
                lambda ctrl: ctrl.getNodeId() == point.getNodeId(),
                self.objects))
            if point != []:
                return point[0]
        return None

    def select_cb(self, event_callback):
        event = event_callback.getEvent()
        if (event.getState() == coin.SoMouseButtonEvent.DOWN and
                event.getButton() == event.BUTTON1):
            pos = event.getPosition()
            obj = self.SendRay(pos)
            self.Select(obj, event.wasCtrlDown())

    def select_all_cb(self, event_callback):
        event = event_callback.getEvent()
        if (event.getKey() == ord('a')):
            if event.getState() == event.DOWN:
                if self.selected_objects:
                    for o in self.selected_objects:
                        o.unselect()
                    self.selected_objects = []
                else:
                    for obj in self.objects:
                        if obj.dynamic:
                            self.selected_objects.append(obj)
                self.ColorSelected()
                self.selection_changed()

    def deselect_all(self):
        if self.selected_objects:
            for o in self.selected_objects:
                o.unselect()
            self.selected_objects = []


    def drag_cb(self, event_callback, force=False):
        event = event_callback.getEvent()
        if ((type(event) == coin.SoMouseButtonEvent and
                event.getState() == coin.SoMouseButtonEvent.DOWN
                and event.getButton() == coin.SoMouseButtonEvent.BUTTON1) or
                force):
            self.register(self.view)
            if self.drag:
                self.view.removeEventCallbackPivy(
                    coin.SoEvent.getClassTypeId(), self.drag)
                self._direction = None
            self.drag = None
            self.start_pos = None
            for obj in self.drag_objects:
                obj.drag_release()
            for foo in self.on_drag_release:
                foo()
        elif (type(event) == coin.SoKeyboardEvent and
                event.getState() == coin.SoMouseButtonEvent.DOWN):
            if event.getKey() == 65307:     # esc
                for obj in self.drag_objects:
                    obj.drag([0, 0, 0], 1)  # set back to zero
                self.drag_cb(event_callback, force=True)
                return
            try:
                key = chr(event.getKey())
            except ValueError:
                # there is no character for this value
                key = '_'
            if key in 'xyz' and key != self._direction:
                self._direction = key
            else:
                self._direction = None
            diff = self.cursor_pos(event) - self.start_pos
            diff = self.constrained_vector(diff)
            # self.start_pos = self.cursor_pos(event)
            for obj in self.drag_objects:
                obj.drag(diff, 1)
            for foo in self.on_drag:
                foo()

        elif type(event) == coin.SoLocation2Event:
            fact = 0.3 if event.wasShiftDown() else 1.
            diff = self.cursor_pos(event) - self.start_pos
            diff = self.constrained_vector(diff)
            # self.start_pos = self.cursor_pos(event)
            for obj in self.drag_objects:
                obj.drag(diff, fact)
            for foo in self.on_drag:
                foo()

    def grab_cb(self, event_callback, force=False):
        # press g to move an entity
        event = event_callback.getEvent()
        # get all drag objects, every selected object can add some drag objects
        # but the eventhandler is not allowed to call the drag twice on an object
        if event.getKey() == ord('g') or force:
            self.drag_objects = set()
            for i in self.selected_objects:
                for j in i.drag_objects:
                    self.drag_objects.add(j)
            # check if something is selected
            if self.drag_objects:
                # first delete the selection_cb, and higlight_cb
                self.unregister()
                # now add a callback that calls the dragfunction of the selected entites
                self.start_pos = self.cursor_pos(event)
                self.drag = self.view.addEventCallbackPivy(
                    coin.SoEvent.getClassTypeId(), self.drag_cb)
                for obj in self.drag_objects:
                    obj.drag_start()
                for foo in self.on_drag_start:
                    foo()

    def delete_cb(self, event_callback):
        event = event_callback.getEvent()
        # get all drag objects, every selected object can add some drag objects
        # but the eventhandler is not allowed to call the drag twice on an object
        if event.getKey() == ord(u'\uffff') and (event.getState() == 1):
            self.removeSelected()

    def register(self, view):
        self.view = view
        self.mouse_over = self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over_cb)
        self.select = self.view.addEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select_cb)
        self.grab = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.grab_cb)
        self.delete = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.delete_cb)
        self.select_all = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all_cb)

    def unregister(self):
        self.view.removeEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over)
        self.view.removeEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.grab)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.delete)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all)

    def removeSelected(self):
        temp = []
        for i in self.selected_objects:
            i.delete()
        for i in self.objects + self.static_objects:
            i.check_dependency()    #dependency length max = 1
        for i in self.objects + self.static_objects:
            if i._delete:
                temp.append(i)
        self.selected_objects = []
        self.over_object = None
        for i in temp:
            if i in self.objects:
                self.objects.remove(i)
            else:
                self.static_objects.remove(i)
            self.removeChild(i)
        self.selection_changed()

    def removeAllChildren(self):
        for i in self.objects:
            i.delete()
        self.objects = []
        self.static_objects = []
        super(InteractionSeparator, self).removeAllChildren()

    def constrained_vector(self, vector):
        if self._direction is None:
            return vector
        if self._direction == 'x':
            return [vector[0], 0, 0]
        elif self._direction == 'y':
            return [0, vector[1], 0]
        elif self._direction == 'z':
            return [0, 0, vector[2]]
