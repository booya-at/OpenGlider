from __future__ import annotations

from typing import TYPE_CHECKING, Any
from openglider.glider.ballooning.base import BallooningBase
from openglider.glider.project import GliderProject

from openglider.gui.qt import QtWidgets, QtGui, QtCore
import euklid

from openglider.glider.ballooning import BallooningBezierNeu, Ballooning
from openglider.gui.views_2d import Canvas, DraggableLine
from openglider.gui.wizzards.base import SelectionWizard
from openglider.utils.colors import Color

if TYPE_CHECKING:
    from openglider.gui.app.main_window import MainWindow

class Ballooning2D(QtWidgets.QGraphicsObject):
    def __init__(self, ballooning: BallooningBezierNeu, color: Color=None, alpha: int=160):
        super().__init__()
        self.ballooning = ballooning
        self.color = color or Color(255, 0, 0)
        self.alpha = alpha

    def paint(self, p: QtGui.QPainter, *args: Any) -> None:
        color = QtGui.QColor(*self.color.rgb(), self.alpha)
        pen = QtGui.QPen(QtGui.QBrush(color), 1)
        pen.setCosmetic(True)
        p.setPen(pen)

        points = self.ballooning.get_points(150)
        points_qt = [QtCore.QPointF(*p) for p in points]

        for p1, p2 in zip(points_qt[:-1], points_qt[1:]):
            p.drawLine(p1, p2)

        #p.drawRect(self.boundingRect())

    def boundingRect(self) -> QtCore.QRectF:
        amount_max = self.ballooning.amount_maximal

        return QtCore.QRectF(-1, 0, 2, amount_max)


class BallooningInput(Canvas):
    balloonings: list[BallooningBase]
    ballooning: BallooningBezierNeu
    ballooning_curve: DraggableLine | None
    ballooning_line: Ballooning2D | None
    locked_aspect_ratio = False

    def __init__(self, ballooning: BallooningBase):
        super().__init__(parent=None)
        self.balloonings = []
        self.ballooning_line = None
        self.ballooning_curve = None

        self.set_ballooning(ballooning)

    def set_ballooning(self, ballooning: BallooningBase) -> None:
        if not isinstance(ballooning, BallooningBezierNeu):
            raise ValueError()

        if getattr(self, "ballooning", None) is not None:
            if self.ballooning_curve is not None:
                self.ballooning_curve.on_node_move.clear()
                self.ballooning_curve.on_node_release.clear()
                self.removeItem(self.ballooning_curve)
            if self.ballooning_line is not None:
                self.removeItem(self.ballooning_line)

        self.ballooning = ballooning
        self.ballooning_curve = DraggableLine(ballooning.controlpoints.nodes)

        self.ballooning_curve.on_node_move.append(self.on_node_move)

        self.addItem(self.ballooning_curve)
        self.ballooning_line = Ballooning2D(self.ballooning, Color(255, 255, 255), 160)
        self.addItem(self.ballooning_line)

    def draw_balloonings(self, balloonings: list[tuple[BallooningBase, Color]]) -> None:
        for ballooning in self.balloonings:
            self.removeItem(ballooning)
        self.balloonings.clear()

        for ballooning, color in balloonings:
            if not isinstance(ballooning, BallooningBezierNeu):
                raise ValueError()
            ballooning_2d = Ballooning2D(ballooning, color, 100)
            self.balloonings.append(ballooning_2d)  # type: ignore
            self.addItem(ballooning_2d)

    def on_node_move(self, curve: DraggableLine, event: Any) -> None:
        node_index = curve.drag_node_index

        if node_index is None or self.ballooning_curve is None:
            raise ValueError()

        if node_index + 1 == len(curve.controlpoints):
            curve.data["pos"][node_index][0] = 1.
            curve.data["pos"][0][1] = curve.data["pos"][node_index][1]
        elif node_index == 0:
            curve.data["pos"][node_index][0] = -1.
            curve.data["pos"][-1][1] = curve.data["pos"][node_index][1]

        self.ballooning.controlpoints = euklid.vector.PolyLine2D(self.ballooning_curve.controlpoints)

        self.update()


class BallooningWidget(SelectionWizard):
    widget_name = "Ballooning"
    
    def __init__(self, app: MainWindow, project: GliderProject):
        balloonings: list[tuple[BallooningBase, str]] = []
        for _project in app.state.projects:
            for i, ballooning in enumerate(_project.glider.balloonings):
                balloonings.append((
                    ballooning,
                    f"{_project.name}/{i}/{ballooning.name}"
                ))
        super().__init__(app, project, balloonings)

        # replace balloonings
        balloonings_new: list[BallooningBase] = []

        for ballooning in self.project.glider.balloonings:
            if isinstance(ballooning, Ballooning):
                ballooning = BallooningBezierNeu.from_classic(ballooning)

            balloonings_new.append(ballooning)

        self.project.glider.balloonings = balloonings_new

        self.ballooning_input = BallooningInput(self.project.glider.balloonings[0])

        self.selector = QtWidgets.QComboBox()
        self.selector.activated.connect(self.select_ballooning)
        self.main_widget.addWidget(self.selector)
        self.main_widget.addWidget(self.ballooning_input.get_widget())

        for i, ballooning in enumerate(self.project.glider.balloonings):
            self.selector.addItem(f"{self.project.name}/{i} ({ballooning.name})")

    def select_ballooning(self, i: int) -> None:
        self.ballooning_input.set_ballooning(self.project.glider.balloonings[i])

    def selection_changed(self, selected: list[tuple[BallooningBase, Color]]) -> None:
        self.ballooning_input.draw_balloonings(selected)

    def apply(self, update: bool=True) -> None:
        self.project.glider.apply_ballooning(self.project.glider_3d)
        super().apply(update)
