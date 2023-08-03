from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
from collections.abc import Callable

import euklid
from openglider.glider.curve import CurveEnum, GliderCurveType, ShapeBSplineCurve
from openglider.glider.project import GliderProject
from openglider.glider.shape import Shape
from openglider.gui.state.selection_list.list import SelectionList, SelectionListItem
from openglider.gui.qt import QtCore, QtWidgets
from openglider.gui.views.compare.shape import ShapeConfigWidget
from openglider.gui.views_2d import Canvas, DraggableLine, Line2D
from openglider.gui.views_2d.canvas import LayoutGraphics
from openglider.gui.widgets.list_select import ListWidget
from openglider.gui.widgets.select import EnumSelection
from openglider.gui.widgets.table import QTable
from openglider.gui.wizzards.base import Wizard
from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.utils.table import Table

from openglider.gui.app.main_window import MainWindow

logger = logging.getLogger(__name__)
# TODO: Show & change data: Area, Aspect ratio, Span, Tip Chord, Tip center


class CurveInput(Canvas):
    changed = QtCore.Signal()

    locked_aspect_ratio: bool = True
    drag_line: DraggableLine | None = None

    shape: Shape
    curves: SelectionList[GliderCurveType, SelectionListItem[GliderCurveType]]
    active_curve: SelectionListItem[GliderCurveType] | None = None
    layout_graphics: LayoutGraphics | None
    on_change: list[Callable]

    def __init__(self, project: GliderProject, curves: SelectionList[GliderCurveType, SelectionListItem[GliderCurveType]]):
        super().__init__(parent=None)

        self.on_change = []
        self.glider_shape = project.glider.shape.copy()
        self.curves = curves

        self.shape_plot = ShapePlot(project)
        self.shape_settings = ShapeConfigWidget()
        self.shape_settings.changed.connect(self.draw_shape)


        self.curve_shapes: dict[str, tuple[Line2D, Line2D]] = {}
        self.layout_graphics = None
        self.draw_shape()
    
    def draw_shape(self) -> None:
        if self.layout_graphics is not None:
            self.removeItem(self.layout_graphics)
        config = self.shape_settings.get_config()
        dwg = self.shape_plot.redraw(config[0] + config[1])

        self.layout_graphics = LayoutGraphics(self.shape_plot.drawing, fill=False)
        self.addItem(self.layout_graphics)

    def draw_curves(self, clear: bool=True, normalize_area: bool=False, normalize_span: bool=False) -> None:
        # list of glider projects
        if clear:
            for curve1, curve2 in self.curve_shapes.values():
                self.removeItem(curve1)
                self.removeItem(curve2)
            self.curve_shapes = {}

        for curve in self.curves.filter_active():
            points = curve.element.draw()
            
            curve_2d_l = Line2D(points.mirror().reverse().nodes, curve.color)
            curve_2d_r = Line2D(points.nodes, curve.color)

            self.addItem(curve_2d_l)
            self.addItem(curve_2d_r)
            self.curve_shapes[curve.name] = (curve_2d_l, curve_2d_r)

        if (selected := self.curves.get_selected_wrapped()) is not None:
            self.edit(selected)

        self.update()

    def edit(self, curve: SelectionListItem[GliderCurveType]) -> None:
        if self.drag_line is not None:
            self.removeItem(self.drag_line)

        self.active_curve = curve
        self.drag_line = DraggableLine(curve.element.controlpoints_2d)

        self.drag_line.on_node_move.append(self.on_node_move)
        self.drag_line.on_node_release.append(self.on_node_release)

        self.addItem(self.drag_line)

    def on_node_move(self, curve: GliderCurveType, event: Any) -> None:
        if self.active_curve is None or self.drag_line is None:
            raise ValueError()
        
        self.active_curve.element.set_controlpoints_2d(self.drag_line.controlpoints.nodes)
        self.drag_line.set_controlpoints(self.active_curve.element.controlpoints_2d)

        points = self.active_curve.element.draw()
        curve_l, curve_r = self.curve_shapes[self.active_curve.name]
        curve_l.curve_data = points.mirror().reverse().nodes
        curve_r.curve_data = points.nodes


        self.update()

    def on_node_release(self, curve: GliderCurveType, event: Any) -> None:
        self.changed.emit()
    
    def get_widget(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        widget.setLayout(QtWidgets.QVBoxLayout())
        widget.layout().addWidget(self.shape_settings)
        widget.layout().addWidget(super().get_widget())

        return widget


class CurveSettings(QtWidgets.QWidget):
    changed = QtCore.Signal()

    curve: SelectionListItem[GliderCurveType] | None

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.curve = None

        self.setLayout(QtWidgets.QVBoxLayout())

        self.curve_type_selector = EnumSelection(CurveEnum, self)
        self.curve_type_selector.changed.connect(self.update_curve_type)
        self.layout().addWidget(self.curve_type_selector)

        self.nodes_table = QTable()
        self.layout().addWidget(self.nodes_table)

        self.update_curve()

    def set_active(self, curve: SelectionListItem[GliderCurveType]) -> None:
        self.curve = curve
        if self.curve is not None:
            self.curve_type_selector.select(curve.element.__class__)
        
        self.update_curve()

    def update_curve(self) -> None:
        table = Table()
        table[0,0] = "X"
        table[0, 1] = "Y"

        if self.curve is not None:
            for i, node in enumerate(self.curve.element.controlpoints):
                table[i+1, 0] = node[0]
                table[i+1, 1] = node[1]
        
        self.nodes_table.push_table(table)

    def update_curve_type(self) -> None:
        curve_cls = self.curve_type_selector.selected.value

        if self.curve is not None:
            points = self.curve.element.controlpoints
            shape = self.curve.element.shape
            self.curve.element = curve_cls(points, shape)
        
        self.changed.emit()


class CurveWizard(Wizard):
    def __init__(self, app: MainWindow, project: GliderProject):
        super().__init__(app=app, project=project)

        self.setLayout(QtWidgets.QHBoxLayout())

        self.main_widget = QtWidgets.QSplitter()
        self.main_widget.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.layout().addWidget(self.main_widget)

        self.right_widget = QtWidgets.QWidget()
        self.right_widget.setLayout(QtWidgets.QVBoxLayout())

        self.shape = self.project.glider.shape.get_half_shape()

        self.curve_list = SelectionList[GliderCurveType, SelectionListItem[GliderCurveType]]()
        self.curve_list_selector = ListWidget(self, self.curve_list)


        self.curve_input = CurveInput(self.project, self.curve_list)
        self.curve_settings = CurveSettings(self)

        self.right_widget.layout().addWidget(self.curve_list_selector)
        self.right_widget.layout().addWidget(self.curve_settings)

        self.curves = project.glider.get_curves()

        for name, curve in self.curves.items():
            self.curve_list.add(name, curve)

        self.curve_add_button = QtWidgets.QPushButton("Add Curve")
        self.curve_add_button.clicked.connect(self.add_curve)
        self.right_widget.layout().addWidget(self.curve_add_button)
        
        self.curve_list_selector.render()
        self.curve_list_selector.changed.connect(self.selection_changed)
        self.curve_settings.changed.connect(self.selection_changed)
        self.curve_input.changed.connect(self.curve_settings.update_curve)

        self.button_apply = QtWidgets.QPushButton("Apply")
        self.button_apply.clicked.connect(self.apply)

        self.right_widget.layout().addWidget(self.button_apply)


        self.main_widget.addWidget(self.curve_input.get_widget())
        self.main_widget.addWidget(self.right_widget)
        self.main_widget.setSizes([800, 200])


        self.selection_changed()

    def _update(self) -> None:
        pass
    
    def add_curve(self) -> None:
        p1 = euklid.vector.Vector2D([1., 0.5])
        p2 = euklid.vector.Vector2D([2., 0.5])
        p3 = euklid.vector.Vector2D([self.shape.rib_no-1, 0.5])
        self.curve_list.add("unnamed", ShapeBSplineCurve([p1, p2, p3], self.shape))
        self.curve_list_selector.render()
        self.selection_changed()


    def apply(self, update: bool=True) -> None:
        curves = {value.name: value.element for value in self.curve_list.elements.values()}
        self.project.glider.tables.curves.apply_curves(curves)
        self.project.update_all()

        super().apply(True)

    def selection_changed(self, item: Any=None) -> None:
        # todo: create color wheel & show
        self.curve_input.draw_curves()

        selected_curve = self.curve_list.get_selected_wrapped()
        if selected_curve is not None:
            self.curve_settings.set_active(selected_curve)
