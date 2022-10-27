from typing import Any, List, Tuple
from openglider.glider.parametric.arc import ArcCurve
from openglider.gui.qt import QtWidgets, QtGui, QtCore
from openglider.utils.colors import Color
import pyqtgraph
import euklid

from openglider.glider.project import GliderProject


class Arc2D(QtWidgets.QGraphicsObject):
    positions: euklid.vector.PolyLine2D
    bbox: Tuple[float, float, float, float]

    def __init__(self, project: GliderProject, color: Color | None=None, alpha: int=160) -> None:
        super().__init__()
        self.project = project
        self.color = color or Color(255,0,0)
        self.alpha = alpha
        
        self.update_arc()

    def get_normalized_arc(self) -> Tuple[ArcCurve, List[float]]:
        new_arc = self.project.glider.arc.copy()
        x_values = self.project.glider.shape.rib_x_values
        max_x = max(x_values)

        x_values_normalized = [x/max_x for x in x_values]

        new_arc.rescale(x_values_normalized)
        return new_arc, x_values_normalized

    def update_arc(self) -> None:
        self.positions = self.get_arc_positions()

        x = [p[0] for p in self.positions.nodes]
        y = [p[1] for p in self.positions.nodes]

        min_x = min(x)
        min_y = min(y)

        width = max(x) - min_x
        height = max(y) - min_y
        self.bbox = min_x, min_y, width, height

    def get_arc_positions(self) -> euklid.vector.PolyLine2D:
        arc, x_values = self.get_normalized_arc()
        points = arc.get_arc_positions(x_values)

        points_left = points * euklid.vector.Vector2D([-1, 1])
        #points_left = [[-p[0], p[1]] for p in points]

        return points_left.reverse() + points

    def paint(self, p: QtGui.QPainter, *args: Any) -> None:
        color = QtGui.QColor(*self.color, self.alpha)
        pen = QtGui.QPen(QtGui.QBrush(color), 1)
        pen.setCosmetic(True)
        p.setPen(pen)

        #points = self.get_arc_positions()

        points_qt = [QtCore.QPointF(*p) for p in self.positions]

        for p1, p2 in zip(points_qt[:-1], points_qt[1:]):
            p.drawLine(p1, p2)

        #p.drawRect(self.boundingRect())

    def boundingRect(self) -> QtCore.QRectF:
        return QtCore.QRectF(*self.bbox)
