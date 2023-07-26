import logging
from typing import Any, Callable, List

import euklid

from openglider.glider.project import GliderProject
from openglider.gui.app.main_window import MainWindow
from openglider.gui.qt import QtCore, QtWidgets
from openglider.gui.views_2d import Canvas, DraggableLine, Line2D
from openglider.gui.wizzards.base import Wizard
from openglider.utils.types import CurveType

logger = logging.getLogger(__name__)
# TODO: Show & change data: Area, Aspect ratio, Span, Tip Chord, Tip center


class DistributionInput(Canvas):
    on_change: List[Callable]
    locked_aspect_ratio = True
    
    drag_line: DraggableLine | None = None

    def __init__(self, curve: CurveType):
        super().__init__(parent=None)
        self.on_change = []

        self.curve = curve

        self.curve_drawing = Line2D(self.curve.get_sequence(40).nodes)
        self.addItem(self.curve_drawing)
        
        self.active_curve = curve
        self.drag_line = DraggableLine(curve.controlpoints.nodes)

        self.drag_line.on_node_move.append(self.on_node_move)

        self.addItem(self.drag_line)

        self.update()


    def on_node_move(self, curve: DraggableLine, event: Any) -> None:
        self.curve.controlpoints = euklid.vector.PolyLine2D(curve.controlpoints)

        points = self.curve.get_sequence(40)
        self.curve_drawing.curve_data = points.nodes
        
        self.update()


class BallooningCurveWizard(Wizard):
    def __init__(self, app: MainWindow, project: GliderProject):
        super().__init__(app=app, project=project)

        self.setLayout(QtWidgets.QHBoxLayout())

        self.main_widget = QtWidgets.QSplitter()
        self.main_widget.setOrientation(QtCore.Qt.Orientation.Vertical)

        self.splitter = QtWidgets.QSplitter()
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)

        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(self.splitter)

        self.right_widget = QtWidgets.QWidget()
        self.right_widget.setLayout(QtWidgets.QVBoxLayout())

        self.button_apply = QtWidgets.QPushButton("Apply")
        self.button_apply.clicked.connect(self.apply)

        self.right_widget.layout().addWidget(self.button_apply)

        self.splitter.addWidget(self.main_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([800, 200])

        self.curve = self.get_curve(project)

        self.curve_input = DistributionInput(self.curve)

        self.main_widget.addWidget(self.curve_input.get_widget())


    @staticmethod
    def get_curve(project: GliderProject) -> CurveType:
        return project.glider.ballooning_merge_curve.copy()

    def apply(self, update: bool=True) -> None:
        self.project.glider.ballooning_merge_curve = self.curve
        self.project.update_all()

        super().apply(True)


class ProfileDistributionWizzard(BallooningCurveWizard):
    @staticmethod
    def get_curve(project: GliderProject) -> CurveType:
        return project.glider.profile_merge_curve.copy()
    
    def apply(self, update: bool=True) -> None:
        logger.info(f"{self.curve}, {self.curve.controlpoints}")
        self.project.glider.profile_merge_curve = self.curve
        self.project.update_all()

        return super().apply(update)