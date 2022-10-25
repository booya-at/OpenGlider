import logging
from openglider.gui.qt import QtWidgets, QtGui, QtCore
from typing import List, Iterator
import euklid
from typing import Literal, Optional

from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.glider import ParametricGlider

from openglider.glider.cell.panel import Panel, PanelCut
from openglider.utils.dataclass import BaseModel

logging.getLogger(__name__)


class ShapeConfig(BaseModel):
    half_wing: bool = False

    draw_ribs: bool = True
    draw_design_lower: bool = False
    draw_design_upper: bool = True

    scale_area: Optional[float] = None
    scale_span: Optional[float] = None


class Shape2D(QtWidgets.QGraphicsObject):
    shape: ParametricShape

    half_wing: bool=False
    draw_ribs: bool=True
    draw_panels_lower: bool = False
    draw_panels_upper: bool = False

    @classmethod
    def from_glider(cls, glider: ParametricGlider, **kwargs):
        panels = glider.get_panels()
        shape = glider.shape.copy()
        shape._clean()
        return cls(shape, panels, **kwargs)

    def __init__(self, shape: ParametricShape, panels: List[List[Panel]]=None, color=None, alpha=160, config: ShapeConfig=None):
        super().__init__()
        self.shape = shape
        self.shape_r = shape.get_half_shape()
        self.shape_l = self.shape_r.copy().scale(x=-1)
        self.shape_both = self.shape.get_shape()

        self.shapes = [self.shape_r, self.shape_l]

        self.panels = panels or []
        self.config = config or ShapeConfig()

        self.color = color or (255, 0, 0)
        self.alpha = alpha

    def paint(self, p, *args):
        color = QtGui.QColor(*self.color, self.alpha)
        pen = QtGui.QPen(QtGui.QBrush(color), 1)

        pen.setCosmetic(True)
        p.setPen(pen)

        if self.config.half_wing:
            shape = self.shape_r
        else:
            shape = self.shape_both

        if self.config.scale_area is not None:
            shape.area = self.config.scale_area
        elif self.config.scale_span is not None:
            factor = self.config.scale_span / shape.span
            shape.scale(factor, factor)

        front = [QtCore.QPointF(*p) for p in shape.front]
        back = [QtCore.QPointF(*p) for p in shape.back]
        middle = [(f+b)*0.5 for f, b in zip(front, back)]

        for p1, p2 in zip(front[:-1], front[1:]):
            p.drawLine(p1, p2)

        for p1, p2 in zip(back[:-1], back[1:]):
            p.drawLine(p1, p2)

        for p1, p2 in zip(middle[:-1], middle[1:]):
            p.drawLine(p1, p2)

        if self.config.draw_ribs:
            for rib in shape.ribs:
                p1 = QtCore.QPointF(*rib[0])
                p2 = QtCore.QPointF(*rib[1])
                p.drawLine(p1, p2)

        if self.config.draw_design_lower:
            self.paint_design(p, False, True, *args)
            self.paint_design(p, True, True, *args)
        
        if self.config.draw_design_upper:
            self.paint_design(p, False, False, *args)
            self.paint_design(p, True, False, *args)
    
    def _cell_range(self, left: bool):
        start = 0
        end = self.shape.half_cell_num
        if self.shape.has_center_cell and left:
            start = 1

        return range(start, end)

    def paint_design(self, p, left, lower, *args):
        shape = self.shapes[left]

        panels = self.panels

        for cell_no in self._cell_range(left):
            if cell_no >= len(panels):
                return

            cell_panels = panels[cell_no]

            def match(panel):
                if lower:
                    # -> either on the left or on the right it should go further than 0
                    return panel.cut_back.x_left > 0 or panel.cut_back.x_right > 0
                else:
                    # should start before zero at least once
                    return panel.cut_front.x_left < 0 or panel.cut_front.x_right < 0

            cell_side_panels: Iterator[Panel] = filter(match, cell_panels)

            for panel in cell_side_panels:
                panel: Panel

                def normalize_x(val):
                    if lower:
                        return max(val, 0)
                    else:
                        return max(-val, 0)


                def get_cut_line(cut: PanelCut):
                    left = shape.get_point(cell_no, normalize_x(cut.x_left))
                    right = shape.get_point(cell_no+1, normalize_x(cut.x_right))

                    if cut.x_center is not None:
                        center = shape.get_point(cell_no+0.5, normalize_x(cut.x_center))
                        return euklid.spline.BSplineCurve([left, center, right]).get_sequence(8).tolist()
                    
                    return [left, right]
                
                nodes = get_cut_line(panel.cut_front) + get_cut_line(panel.cut_back)[::-1]

                qt_nodes = [QtCore.QPointF(*node) for node in nodes]

                color = QtGui.QColor(*panel.material.get_color_rgb(), self.alpha)
                pen = QtGui.QPen(color)
                brush = QtGui.QBrush(color)
                #pen = QtGui.QPen(QtGui.QBrush(color), 255)

                pen.setCosmetic(True)
                p.setPen(pen)
                p.setBrush(brush)
                p.drawPolygon(qt_nodes)

    def boundingRect(self):
        span = self.shape.span
        chord = self.shape.get_rib_point(0, 1)[1]
        if self.half_wing:
            return QtCore.QRectF(0, 0, span, chord)
        else:
            return QtCore.QRectF(-span, 0, 2 * span, chord)
