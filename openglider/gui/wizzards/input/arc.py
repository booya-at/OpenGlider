from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple
from openglider.gui.app.app import GliderApp
from openglider.gui.qt import QtWidgets, QtGui, QtCore
from openglider.utils.colors import Color
import pyqtgraph
import euklid

from openglider.glider.project import GliderProject
from openglider.gui.views_2d import Canvas, DraggableLine
from openglider.gui.wizzards.base import GliderSelectionWizard
from openglider.gui.views_2d.arc import Arc2D

if TYPE_CHECKING:
    from openglider.gui.app.main_window import MainWindow

class ArcInput(Canvas):
    arcs: List[Arc2D]

    locked_aspect_ratio = True

    def __init__(self, project: GliderProject):
        super().__init__(parent=None)
        self.project = project

        #self.arc, self.x_values = Arc2D.get_normalized_arc(self.project)

        self.arc_2d = Arc2D(self.project, Color(255, 255, 255), 160)

        self.arcs = []
        self.arc_diffs: list[Any] = []
        self.addItem(self.arc_2d)

        self.arc_curve = DraggableLine(self.project.glider.arc.curve.controlpoints.nodes)
        self.normalize_cp()

        self.arc_curve.on_node_move.append(self.on_node_move)
        self.arc_curve.on_node_release.append(self.on_node_release)

        self.addItem(self.arc_curve)
        self.diff_widget = pyqtgraph.PlotWidget()
        self.diff_plot = self.diff_widget.plot()

        self.diff_plot.setData(**self.get_diff(self.project))

    def draw_arcs(self, arcs: List[Tuple[GliderProject, Color]], clear: bool=True) -> None:
        if clear:
            for arc in self.arcs:
                self.removeItem(arc)
            self.arcs = []

        for project, color in arcs:
            arc_2d = Arc2D(project, color, 140)
            self.addItem(arc_2d)
            self.arcs.append(arc_2d)

        self.update()


        for arc in self.arc_diffs:
            self.diff_widget.removeItem(arc)
        self.arc_diffs = []

        for project, color in arcs:
            plot = self.diff_widget.plot()
            plot.setPen(*color)

            plot.setData(**self.get_diff(project))
            self.arc_diffs.append(plot)
    
    @staticmethod
    def get_diff(project: GliderProject) -> Dict[str, List[float]]:
        x_values = project.glider.shape.rib_x_values
        y_values = project.glider.arc.get_cell_angles(x_values, rad=False)

        y2 = [y1-y2 for y2, y1 in zip(y_values[:-1], y_values[1:])]

        if y_values[0] != 0:
            y2.insert(0, y_values[0])
            x_values = x_values[1:]
        else:
            y2.insert(0, y_values[1])
        
        line = euklid.vector.PolyLine2D(list(zip(x_values, y2)))
        line_normalized = line.scale(euklid.vector.Vector2D([1/x_values[-1], 1]))

        p0 = euklid.vector.Vector2D([0,0]) 
        p1 = euklid.vector.Vector2D([0, 1])

        if hasattr(project.glider.arc.curve, "get_curvature"):
            interpolation = project.glider.arc.curve.get_curvature(100)  # type: ignore
            line_mirrored = euklid.vector.PolyLine2D(interpolation.nodes).mirror(p0, p1).reverse()
        else:
            line_mirrored = line_normalized.mirror(p0, p1).reverse()
        
        data = {
            "x": [p[0] for p in line_mirrored + line_normalized],
            "y": [p[1] for p in line_mirrored + line_normalized]
        }

        return data


    def normalize_cp(self) -> None:
        normalized_arc, x_values = self.arc_2d.get_normalized_arc()
        self.arc_curve.set_controlpoints(normalized_arc.curve.controlpoints.nodes)

    def on_node_move(self, curve: DraggableLine, event: Any) -> None:
        node_index = curve.drag_node_index
        curve.data["pos"][node_index][0] = max(0, curve.data["pos"][node_index][0])

        self.project.glider.arc.curve.controlpoints = euklid.vector.PolyLine2D(curve.controlpoints)
        self.arc_2d.update_arc()

        self.update()

    def on_node_release(self, curve: DraggableLine, event: Any) -> None:
        self.normalize_cp()
        self.arc_2d.update_arc()
        self.diff_plot.setData(**self.get_diff(self.project))

        self.update()


class ArcWidget(GliderSelectionWizard):
    def __init__(self, app: MainWindow, project: GliderProject):
        super().__init__(app=app, project=project)
        self.arc_input = ArcInput(self.project)

        self.main_widget.addWidget(self.arc_input.get_widget())
        self.main_widget.addWidget(self.arc_input.diff_widget)

        self.main_widget.setSizes([700, 300])

        #self.right_widget.layout().insertWidget(0, self.input_controls)
        self._selection_changed()

    def selection_changed(self, selected: List[Tuple[GliderProject, Color]]) -> None:
        self.arc_input.draw_arcs(selected)

    def apply(self, update: bool=True) -> None:
        #self.project.glider.arc.curve.controlpoints = self.arc_input.arc.curve.controlpoints
        self.project.glider.rescale_curves()
        self.project.glider.apply_shape_and_arc(self.project.glider_3d)
        self.project.glider_3d.lineset.recalc(glider=self.project.glider_3d)
        super().apply(False)

