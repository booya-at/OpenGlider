from __future__ import annotations

from typing import Any
from collections.abc import Callable

import numpy as np
from matplotlib import image

import pyqtgraph
from pyqtgraph.graphicsItems.ScatterPlotItem import SpotItem, ScatterPlotItem
import pyqtgraph.GraphicsScene.mouseEvents
from openglider.gui.qt import QtCore, QtGui, QtWidgets
import logging

import euklid

from openglider.utils.colors import Color


logger = logging.getLogger(__name__)


class Line2D(QtWidgets.QGraphicsObject):
    color: Color

    def __init__(self, data: list[euklid.vector.Vector2D], color: tuple[int, int, int] | Color | None=None, dashed: bool=False) -> None:
        self.curve_data = data or []
        if isinstance(color, Color):
            self.color = color
        elif isinstance(color, tuple):
            self.color = Color(color[0], color[1], color[2])
        else:
            self.color = Color(255, 255, 255)
            
        self.dashed = dashed
        super().__init__()

    def paint(self, p: QtGui.QPainter, *args: Any) -> None:
        if not self.curve_data:
            return
            
        color = QtGui.QColor(*self.color.rgb(), 255)
        #pen = QtGui.QPen(color)
        pen = QtGui.QPen(QtGui.QBrush(color), 1)

        if self.dashed:
            pen.setStyle(QtCore.Qt.PenStyle.DashLine)

        pen.setCosmetic(True)
        p.setPen(pen)
        #p.setPen(pyqtgraph.mkPen(*self.color))

        nodes = [QtCore.QPointF(*p) for p in self.curve_data]

        for p1, p2 in zip(nodes[:-1], nodes[1:]):
            p.drawLine(p1, p2)

        #p.drawRect(self.boundingRect())
    def boundingRect(self) -> QtCore.QRectF:
        if len(self.curve_data):
            x=[p[0] for p in self.curve_data]
            y=[p[1] for p in self.curve_data]
            return QtCore.QRectF(min(x), min(y), max(x)-min(x), max(y) - min(y))
        
        return QtCore.QRectF(0,0,1,1)


class Image(pyqtgraph.ImageItem):
    point_radius = 10
    is_scaling = False
    is_transforming = False

    def __init__(self, image: np.ndarray, *args: Any, **kwargs: Any) -> None:
        super().__init__(image[::-1], opacity=0.5, *args, **kwargs)
        self.setOpts(axisOrder='row-major')
        self.setZValue(-1)
        
        self.p1 = QtCore.QPointF(0, 0)

        shape = image.shape
        size = 8.
        self.p2 = QtCore.QPointF(size, size * shape[0]/shape[1])

        self._update_rect()
        
    def _update_rect(self) -> None:
        self._rect = QtCore.QRectF(self.p1, self.p2)
        self.setRect(self._rect)

    def paint(self, p: QtGui.QPainter, *args: Any) -> None:
        color = QtGui.QColor(255, 0, 0, 255) # rgba
        pen = QtGui.QPen(QtGui.QBrush(color), 1)
        #pen.setCosmetic(True)
        p.setPen(pen)
        p.setBrush(QtGui.QBrush(color))      

        rect = super().boundingRect()

        point_size = self._get_point_dims()
        p.drawEllipse(rect.bottomRight(), point_size.x(), point_size.y())
        p.drawEllipse(rect.topLeft(), point_size.x(), point_size.y())
        return super().paint(p, *args)

    
    def _get_point_dims(self) -> QtCore.QPointF:
        width = self.pixelWidth()
        height = self.pixelHeight()

        return QtCore.QPointF(self.point_radius*width, self.point_radius*height)

    def scale_to_viewport(self, point: QtCore.QPointF) -> QtCore.QPointF:
        vt = self.viewTransform()
        if vt is None:
            return QtCore.QPointF(self.point_radius, self.point_radius)
        #vt = pyqtgraph.functions.invertQTransform(vt)
        v1 = vt.map(QtCore.QLineF(0, 0, 1, 0)).length()
        v2 = vt.map(QtCore.QLineF(0, 0, 0, 1)).length()

        return QtCore.QPointF(point.x() * v1, point.y() * v2)


    def clickEvent(self, ev: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if ev.button() & QtCore.Qt.MouseButton.LeftButton:
            ev.accept()

            if self.is_transforming or self.is_scaling:
                self.is_scaling = False
                self.is_transforming = False
                return

            position = self.mapToView(ev.pos())
            points_dim = self.scale_to_viewport(self._get_point_dims())

            rect1 =  QtCore.QRectF(self.p1-points_dim, self.p1+points_dim)
            if rect1.contains(position):
                self.is_transforming = position

            rect2 =  QtCore.QRectF(self.p2-points_dim, self.p2+points_dim)
            if rect2.contains(position):
                self.is_scaling = bool(position)

    def dragEvent(self, point: QtCore.QPointF) -> None:
        if self.is_scaling or self.is_transforming:
            coords = self.mapToView(self.mapFromDevice(point))

            if self.is_transforming:
                diff = (coords - self.is_transforming)
                self.p1 = self.p1 + diff
                self.p2 = self.p2 + diff
                self.is_transforming = coords
            
            elif self.is_scaling:
                x1 = coords.x() - self.p1.x()
                x2 = self.p2.x() - self.p1.x()
                #diff = (coords - self.p2)
                self.p2 = self.p1 + (self.p2 - self.p1) * (x1/x2)
                #self.is_scaling = self.p2
            
            self._update_rect()

    def boundingRect(self) -> QtCore.QRectF:
        rect = super().boundingRect()
        dim = self._get_point_dims()

        rect_new = QtCore.QRectF(rect.topLeft()-dim, rect.bottomRight()+dim)

        return rect_new

    @classmethod
    def read_pdf(cls, path: str) -> Image:
        raise NotImplementedError()

    @classmethod
    def read_jpg(cls, path: str) -> Image:
        img = image.imread(path)
        return cls(img)


class DraggableLine(pyqtgraph.GraphItem):
    on_node_move: list[Callable[[DraggableLine, Any], None]]
    on_node_release: list[Callable[[DraggableLine, Any], None]]

    data: dict[str, Any]
    drag_node_index: int | None

    def __init__(self, data: list[euklid.vector.Vector2D]) -> None:
        self.drag_node_index = None
        self.drag_start_position = None
        self.on_node_move = []
        self.on_node_release = []
        self.data = {
            "size": 10,
            "pxMode": True,
        }
        super().__init__()
        self.scatter.sigClicked.connect(self.mouseClickEvent)
        self.set_controlpoints(data)

    @property
    def controlpoints(self) -> euklid.vector.PolyLine2D:
        return euklid.vector.PolyLine2D(self.data["pos"].tolist())

    def set_controlpoints(self, controlpoints: list[euklid.vector.Vector2D]) -> None:
        if isinstance(controlpoints, euklid.vector.PolyLine2D):
            controlpoints = controlpoints.nodes

        num = len(controlpoints)
        data = np.empty(num, dtype=[('index', int)])
        data['index'] = np.arange(num)

        self.data["data"] = data
        self.data["adj"] = np.column_stack((np.arange(0, num-1), np.arange(1, num)))
        self.data["pos"] = np.array(controlpoints)

        self.updateGraph()

    def updateGraph(self) -> None:
        super().setData(**self.data)

    def mouseClickEvent(self, scatter: SpotItem, points: ScatterPlotItem, ev: QtGui.QMouseEvent) -> None:
        keys = ev.modifiers()

        is_ctrl_key = (keys == QtCore.Qt.KeyboardModifier.ControlModifier)
        is_shift_key = (keys == QtCore.Qt.KeyboardModifier.ShiftModifier)

        if is_ctrl_key or is_shift_key:
            node_index = points[0].data()[0]
            controlpoints = euklid.vector.PolyLine2D(self.data["pos"].tolist())

            if is_ctrl_key:
                if node_index in (0, len(controlpoints)-1):
                    return
                
                new_segment = controlpoints.nodes[0:node_index]
                new_segment += controlpoints.nodes[node_index+1:]

            elif is_shift_key:
                if node_index == len(controlpoints)-1:
                    return

                new_segment = controlpoints.nodes[0:node_index+1]  # include node_index
                new_segment.append(controlpoints.get(node_index+0.5))
                new_segment += controlpoints.nodes[node_index+1:]

            self.set_controlpoints(new_segment)
            self.updateGraph()

            self.drag_node_index = node_index
            for f in self.on_node_move:
                f(self, ev)
            self.drag_node_index = None
            for f in self.on_node_release:
                f(self, ev)

        else:
            ev.accept()

    def mouseDragEvent(self, ev: pyqtgraph.GraphicsScene.mouseEvents.MouseDragEvent) -> None:
        if ev.button() != QtCore.Qt.MouseButton.LeftButton:
            ev.ignore()
            return

        if ev.isStart():
            pos = ev.buttonDownPos()
            pts = self.scatter.pointsAt(pos)
            if len(pts) == 0:
                ev.ignore()
                return

            self.drag_node_index = pts[0].data()[0]
            self.drag_start_position = self.data['pos'][self.drag_node_index] - pos

            self.drag_start_node_position = self.data['pos'][self.drag_node_index].tolist() 
            
        elif ev.isFinish():
            for f in self.on_node_release:
                f(self, ev)
            self.drag_node_index = None
            return

        elif self.drag_node_index is None:
            ev.ignore()
            return

        ind = self.drag_node_index


        new_position = list(ev.pos() + self.drag_start_position)

        if ev.modifiers() == QtCore.Qt.KeyboardModifier.ShiftModifier:
            diff_x = abs(new_position[0] - self.drag_start_node_position[0])
            diff_y = abs(new_position[1] - self.drag_start_node_position[1])

            if diff_x > diff_y:
                new_position[1] = self.drag_start_node_position[1]
            else:
                new_position[0] = self.drag_start_node_position[0]
            
            
               
        self.data['pos'][ind] = new_position



        #self.data['pos'][ind] = ev.pos() + self.drag_start_position
        for f in self.on_node_move:
            f(self, ev)

        self.updateGraph()
        ev.accept()