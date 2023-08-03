from __future__ import annotations

import math
from typing import Any, TYPE_CHECKING

import euklid
from openglider.glider.project import GliderProject
from openglider.gui.qt import QtCore, QtGui, QtWidgets
from openglider.gui.views_2d import Canvas, DraggableLine
from openglider.gui.widgets.input import NumberInput
from openglider.gui.wizzards.base import GliderSelectionWizard
from openglider.utils.colors import Color, colorwheel

if TYPE_CHECKING:
    from openglider.gui.app.main_window import MainWindow

class AOA2D(QtWidgets.QGraphicsObject):
    def __init__(self, project: GliderProject, color: Color=None, alpha: int=160):
        super().__init__()
        self.project = project
        self.color = color or Color(255, 0, 0)
        self.alpha = alpha

    def paint(self, p: QtGui.QPainter, *args: Any) -> None:
        color = QtGui.QColor(*self.color.rgb(), self.alpha)
        pen = QtGui.QPen(QtGui.QBrush(color), 1)
        pen.setCosmetic(True)
        p.setPen(pen)

        x_values = self.project.glider.shape.rib_x_values
        span = x_values[-1]
        x_normalized = [x/span for x in x_values]

        aoa_absolute = [rib.aoa_absolute * 180 / math.pi for rib in self.project.glider_3d.ribs]
        aoa_relative = [rib.aoa_relative * 180 / math.pi for rib in self.project.glider_3d.ribs]

        points_absolute = []
        points_relative = []

        for i, x in enumerate(x_normalized):
            points_absolute.append(QtCore.QPointF(x, aoa_absolute[i]))
            points_relative.append(QtCore.QPointF(x, aoa_relative[i]))

        for i in range(len(x_normalized) - 1):
            p.drawLine(points_relative[i], points_relative[i+1])

        pen.setStyle(QtCore.Qt.PenStyle.DashLine)
        pen.setWidth(2)
        p.setPen(pen)

        for i in range(len(x_normalized) - 1):
            p.drawLine(points_absolute[i], points_absolute[i+1])

    def boundingRect(self) -> QtCore.QRectF:
        aoa_absolute = [rib.aoa_absolute * 180 / math.pi for rib in self.project.glider_3d.ribs]
        aoa_relative = [rib.aoa_relative * 180 / math.pi for rib in self.project.glider_3d.ribs]

        lower = min(aoa_absolute + aoa_relative)
        upper = max(aoa_absolute + aoa_relative)

        return QtCore.QRectF(0, lower, 1, upper-lower)


class AOAInput(Canvas):
    aoas: list[AOA2D]

    locked_aspect_ratio = False

    def __init__(self, project: GliderProject):
        super().__init__(parent=None)
        self.project = project

        cp = self.normalize(self.project.glider.aoa.controlpoints)
        self.arc_curve = DraggableLine(cp.nodes)

        self.arc_curve.on_node_move.append(self.on_node_move)

        self.addItem(self.arc_curve)

        self.aoa_2d = AOA2D(self.project, Color(255, 255, 255), 160)

        self.aoas = []
        self.addItem(self.aoa_2d)

    def set_cp(self, cp: euklid.vector.PolyLine2D) -> None:
        cp_new = self.normalize(cp)
        self.arc_curve.set_controlpoints(cp_new.nodes)

    @classmethod
    def normalize(cls, cp: euklid.vector.PolyLine2D) -> euklid.vector.PolyLine2D:
        span = cp.nodes[-1][0]

        # scale x -> [0,1], y [deg]
        return cp  * euklid.vector.Vector2D([1./span, 180./math.pi])

    def draw_aoas(self, projects: list[GliderProject], clear: bool=True) -> None:
        if clear:
            for shape in self.aoas:
                self.removeItem(shape)
            self.aoas = []

        colors = colorwheel(len(projects))

        for color, project in zip(colors, projects):
            shape_2d = AOA2D(project, color, 140)
            self.addItem(shape_2d)
            self.aoas.append(shape_2d)

        self.update()

    def on_node_move(self, curve: DraggableLine, event: Any) -> None:
        node_index = curve.drag_node_index

        if node_index is None:
            raise ValueError()

        if node_index + 1 == len(curve.controlpoints):
            curve.data["pos"][node_index][0] = 1.

        curve.data["pos"][node_index][0] = max(0, curve.data["pos"][node_index][0])#

        span = self.project.glider.aoa.controlpoints.nodes[-1][0]
        controlpoints = euklid.vector.PolyLine2D([[p[0]*span, p[1] * math.pi / 180] for p in curve.controlpoints])
        self.project.glider.aoa.controlpoints = controlpoints
        #self.project.glider.rescale_curves()
        self.project.glider.apply_aoa(self.project.glider_3d)

        self.update()


class AOAWizard(GliderSelectionWizard):
    project: GliderProject
    def __init__(self, app: MainWindow, project: GliderProject):
        super().__init__(app=app, project=project)
        self.shape_input = AOAInput(self.project)


        #self.canvas_controls = CanvasControls(self.shape_input, vertical=True)
        self.main_widget.addWidget(self.shape_input.get_widget())
        self.glide_input = NumberInput(self, "Glide", default=project.glider.glide, places=2)
        self.glide_input.on_changed.append(self.change_glide)
        self.right_widget.layout().addWidget(self.glide_input)
        #self.right_widget.layout().insertWidget(0, self.canvas_controls)
        self._selection_changed()
        self._selection_changed()

    def change_glide(self, value: float) -> None:
        print("change!")
        aoa_absolutes = [rib.aoa_absolute for rib in self.project.glider_3d.ribs]
        self.project.glider.glide = value
        self.project.glider_3d.glide = value

        for aoa, rib in zip(aoa_absolutes, self.project.glider_3d.ribs):
            rib.aoa_absolute = aoa
        
        aoa_curve = self.project.glider.aoa
        numpoints = len(aoa_curve.controlpoints)
        
        aoa_relatives = [rib.aoa_relative for rib in self.project.glider_3d.ribs]
        x_values = self.project.glider.shape.rib_x_values
        if self.project.glider.shape.has_center_cell:
            aoa_relatives = aoa_relatives[1:]

        aoa_value = []
        for x, aoa in zip(x_values, aoa_relatives):
            aoa_value.append([x, aoa])

        #print(type(aoa_curve), aoa_relatives, numpoints)
        self.project.glider.aoa = type(aoa_curve).fit(aoa_value, numpoints)  # type: ignore
        self.project.glider.apply_aoa(self.project.glider_3d)
        self.shape_input.set_cp(self.project.glider.aoa.controlpoints)
        self.shape_input.addItem(AOA2D(self.project, Color(0,255,0)))
        self.shape_input.update()

    def selection_changed(self, selected: list[tuple[GliderProject, Color]]) -> None:
        for shape in self.shape_input.aoas:
            self.shape_input.removeItem(shape)
            self.shape_input.aoas = []

        for project, color in selected:
            aoa = AOA2D(project, color, 140)
            self.shape_input.addItem(aoa)
            self.shape_input.aoas.append(aoa)

        self.shape_input.update()

    def apply(self, update: bool=True) -> None:
        self.project.glider.rescale_curves()
        self.project.glider.apply_shape_and_arc(self.project.glider_3d)
        self.project.glider_3d.lineset.recalc(glider=self.project.glider_3d)
        super().apply(False)
