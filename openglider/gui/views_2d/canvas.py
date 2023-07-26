import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import pyqtgraph
from pyqtgraph.GraphicsScene.mouseEvents import MouseDragEvent
from openglider.gui.qt import QtCore, QtGui, QtWidgets
from openglider.gui.views_2d.elements import Image
from openglider.utils.colors import Color
from openglider.vector.drawing import Layout

logger = logging.getLogger(__name__)

#print(type(pyqtgraph.ViewBox))
class Canvas(pyqtgraph.ViewBox):
    grid = True
    locked_aspect_ratio = False
    static = False

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._grid = None
        self.update_data()
        self.setAcceptDrops(True)

    def update_data(self) -> None:
        if self.grid and self._grid is None:
            self._grid = pyqtgraph.GridItem()
            self.addItem(self._grid)
        elif self._grid and not self.grid:
            self.removeItem(self._grid)
            self._grid = None

        self.setAspectLocked(self.locked_aspect_ratio)

        self.update()

    def mouseDragEvent(self, ev: MouseDragEvent, axis: None=None) -> None:
        ev.accept()

        pos = ev.pos()
        last_pos = ev.lastPos()
        diff = -(pos - last_pos)

        ## Scale or translate based on mouse button
        if ev.button() & (QtCore.Qt.MouseButton.LeftButton | QtCore.Qt.MouseButton.MiddleButton):
            if ev.isFinish():  ## This is the final move in the drag; change the view scale now
                #print "finish"
                self.rbScaleBox.hide()
                ax = QtCore.QRectF(pyqtgraph.Point(ev.buttonDownPos(ev.button())), pyqtgraph.Point(pos))
                ax = self.childGroup.mapRectFromParent(ax)
                #self.showAxRect(ax)
                #self.axHistoryPointer += 1
                #self.axHistory = self.axHistory[:self.axHistoryPointer] + [ax]
            else:
                ## update shape of scale box
                self.updateScaleBox(ev.buttonDownPos(), ev.pos())
        elif self.static:
            return
        elif ev.button() & QtCore.Qt.MouseButton.RightButton:
            tr = diff  # *mask
            tr = self.mapToView(tr) - self.mapToView(pyqtgraph.Point(0, 0))
            x = tr.x() # if mask[0] == 1 else None
            y = tr.y() # if mask[1] == 1 else None

            self._resetTarget()
            if x is not None or y is not None:
                self.translateBy(x=x, y=y)
            self.sigRangeChangedManually.emit(self.state['mouseEnabled'])

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e: QtGui.QDropEvent) -> None:
        """
        Drag and Drop glider files
        """
        if e.mimeData().hasUrls():
            e.setDropAction(QtCore.Qt.DropAction.CopyAction)
            e.accept()
            fname = None
            # Workaround for OSx dragging and dropping
            for url in e.mimeData().urls():
                #if op_sys == 'Darwin':
                #    fname = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
                fname = str(url.toLocalFile())
            
            if fname:
                # process file
                logger.info(f"read file: {fname}")
                self.load_bg_image(fname)

        else:
            e.ignore()

    def load_bg_image(self, path: str) -> None:
        background_image = Image.read_jpg(path)
        self.addItem(background_image)

        sc = self.scene()
        sc.sigMouseClicked.connect(background_image.clickEvent)
        sc.sigMouseMoved.connect(background_image.dragEvent)

    def wheelEvent(self, ev: QtGui.QWheelEvent, axis: None=None) -> None:
        if self.static is False:
            super().wheelEvent(ev, axis=axis)

    def get_widget(self) -> pyqtgraph.GraphicsView:
        canvas = pyqtgraph.GraphicsView()
        canvas.setCentralItem(self)
        canvas.setAcceptDrops(True)
        canvas.dragEnterEvent = self.dragEnterEvent
        canvas.dropEvent = self.dropEvent

        return canvas


class CanvasGrid(pyqtgraph.GraphicsLayoutWidget):
    def __init__(self, parent: QtWidgets.QWidget=None):
        super().__init__(parent)

        self.viewbox = Canvas()
        self.setCentralItem(self.viewbox)



class LayoutGraphics(QtWidgets.QGraphicsObject):
    points: Dict[str, List[QtCore.QPointF]]
    lines: Dict[str, List[Tuple[QtCore.QPointF, QtCore.QPointF]]]
    polygons: Dict[str, List[List[QtCore.QPointF]]]
    shown_layers: list[str] | None = None

    bounding_box: QtCore.QRectF | None = None

    def __init__(self, layout: Layout, fill: bool=False, color: Optional[Color]=None):
        super().__init__()
        self.layout: Layout = layout
        self.fill = fill
        self.alpha = 255
        self.color = color
        #self.setAcceptHoverEvents(True)
        #pyqtgraph.GraphicsScene.registerObject(self)
        self.update()

    def update(self) -> None:  # type: ignore
        self.points = {}
        self.lines = {}
        self.polygons = {}

        self.bounding_box = QtCore.QRectF(
            self.layout.min_x,
            self.layout.min_y,
            self.layout.width,
            self.layout.height
        )

        def normalize_color_code(color_code: str) -> str:
            try:
                color=Color.parse_hex(color_code)
                return color.hex()
            except:
                return "ffffff"
            
        
        default_config = self.layout.layer_config.get("*", {})

        for part in self.layout.parts:
            fill_color = None
            if part.material_code and self.fill:
                fill_color_str = re.findall(r".*#([0-9a-fA-f]{3,6})", part.material_code)
                if fill_color_str:
                    fill_color = normalize_color_code(fill_color_str[0])

            for layer_name, layer in part.layers.items():
                if self.shown_layers is not None and layer_name not in self.shown_layers:
                    continue

                layer_config = self.layout.layer_config.get(layer_name, default_config)
                if not layer_config.get("visible", True):
                    continue
                color_code = str(layer_config.get("stroke-color", "#FFFFFF"))


                color = normalize_color_code(color_code)
                #pen = QtGui.QPen(QtGui.QBrush(color), 1)
                #pen.setCosmetic(True)
                #p.setPen(pen)

                for line in layer:
                    points_qt = [QtCore.QPointF(*p) for p in line]

                    if len(line) == 1:
                        self.points.setdefault(color, [])
                        self.points[color].append(points_qt[0])
                    else:
                        if fill_color:
                            self.polygons.setdefault(fill_color, [])
                            self.polygons[fill_color].append(points_qt)
                        else:
                            self.lines.setdefault(color, [])
                            for p1, p2 in zip(points_qt[:-1], points_qt[1:]):
                                self.lines[color].append((p1, p2))
        
        #p.drawRect(self.boundingRect())



    def paint(self, p: QtGui.QPainter, *args: Any) -> None:
        def setup_brush(color_code: str | Color) -> None:
            if isinstance(color_code, str):
                color = Color.parse_hex(color_code)
            else:
                color = color_code

            qt_color = QtGui.QColor(*color.rgb(), self.alpha)

            brush = QtGui.QBrush(qt_color)
            pen = QtGui.QPen(brush, 1)
            pen.setCosmetic(True)
            p.setPen(pen)
            p.setBrush(brush)

        for color_code, points in self.points.items():
            setup_brush(color_code)
            for point in points:
                p.drawPoint(point)
        
        for color_code, lines in self.lines.items():
            if self.color:
                setup_brush(self.color)
            else:
                setup_brush(color_code)
            for line in lines:
                p.drawLine(line[0], line[1])
        
        for color_code, polygons in self.polygons.items():
            setup_brush(color_code)
            for polygon in polygons:
                p.drawPolygon(polygon)


                
    def boundingRect(self) -> QtCore.QRectF:
        return self.bounding_box or QtCore.QRectF(0,0,0,0)
