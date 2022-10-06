from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Optional, Type
import logging
import math
from typing import Tuple, List

import euklid
import numpy as np
from openglider.airfoil import get_x_value
from openglider.glider.cell.panel import Panel, PanelCut
from openglider.glider.cell.diagonals import DiagonalSide, DiagonalRib
from openglider.glider.rib.attachment_point import AttachmentPoint
from openglider.plots.config import PatternConfig
from openglider.plots.cuts import DesignCut
from openglider.plots.glider.diagonal import DribPlot, StrapPlot
from openglider.plots.usage_stats import Material, MaterialUsage
from openglider.utils.config import Config
from openglider.vector.drawing import Layout, PlotPart
from openglider.vector.text import Text

if TYPE_CHECKING:
    from openglider.glider.rib import Rib
    from openglider.glider.cell import Cell

logger = logging.getLogger(__name__)

class PanelPlot(object):
    DefaultConf = PatternConfig
    plotpart: PlotPart
    config: PatternConfig

    panel: Panel
    cell: Cell

    def __init__(self, panel: Panel, cell: Cell, flattended_cell, config=None):
        self.panel = panel
        self.cell = cell
        self.config = self.DefaultConf(config)

        self._flattened_cell = flattended_cell

        self.inner = flattended_cell["inner"]
        self.ballooned = flattended_cell["ballooned"]
        self.outer = flattended_cell["outer"]
        self.outer_orig = flattended_cell["outer_orig"]

        self.x_values = self.cell.rib1.profile_2d.x_values

        self.logger = logging.getLogger(r"{self.__class__.__module__}.{self.__class__.__name__}")

    def flatten(self, attachment_points: List[AttachmentPoint]) -> PlotPart:
        plotpart = PlotPart(material_code=str(self.panel.material), name=self.panel.name)

        _cut_types = PanelCut.CUT_TYPES

        cut_allowances = {
            _cut_types.folded: self.config.allowance_entry_open,
            _cut_types.parallel: self.config.allowance_trailing_edge,
            _cut_types.orthogonal: self.config.allowance_design,
            _cut_types.singleskin: self.config.allowance_entry_open,
            _cut_types.cut_3d: self.config.allowance_design,
            _cut_types.round: self.config.allowance_design
        }

        cut_types: Dict[PanelCut.CUT_TYPES, Type[DesignCut]] = {
            _cut_types.folded: self.config.cut_entry,
            _cut_types.parallel: self.config.cut_trailing_edge,
            _cut_types.orthogonal: self.config.cut_design,
            _cut_types.singleskin: self.config.cut_entry,
            _cut_types.cut_3d: self.config.cut_3d,
            _cut_types.round: self.config.cut_round
        }

        ik_values = self.panel._get_ik_values(self.cell, self.config.midribs, exact=True)

        # get seam allowance
        if self.panel.cut_front.seam_allowance is not None:
            allowance_front = -self.panel.cut_front.seam_allowance
        else:
            allowance_front = -cut_allowances[self.panel.cut_front.cut_type]
        
        if self.panel.cut_back.seam_allowance is not None:
            allowance_back = self.panel.cut_back.seam_allowance
        else:
            allowance_back = cut_allowances[self.panel.cut_back.cut_type]

        # cuts -> cut-line, index left, index right
        self.cut_front = cut_types[self.panel.cut_front.cut_type](amount=allowance_front)
        self.cut_back = cut_types[self.panel.cut_back.cut_type](amount=allowance_back)

        inner_front = [(line, ik[0]) for line, ik in zip(self.inner, ik_values)]
        inner_back = [(line, ik[1]) for line, ik in zip(self.inner, ik_values)]

        shape_3d_amount_front = [-x for x in self.panel.cut_front.cut_3d_amount]
        shape_3d_amount_back = self.panel.cut_back.cut_3d_amount

        if self.panel.cut_front.cut_type != _cut_types.cut_3d:
            dist = np.linspace(shape_3d_amount_front[0], shape_3d_amount_front[-1], len(shape_3d_amount_front))
            shape_3d_amount_front = list(dist)

        if self.panel.cut_back.cut_type != _cut_types.cut_3d:
            dist = np.linspace(shape_3d_amount_back[0], shape_3d_amount_back[-1], len(shape_3d_amount_back))
            shape_3d_amount_back = list(dist)

        left = inner_front[0][0].get(inner_front[0][1], inner_back[0][1])
        right = inner_front[-1][0].get(inner_front[-1][1], inner_back[-1][1])

        outer_left = left.offset(-self.config.allowance_general)
        outer_right = right.offset(self.config.allowance_general)

        cut_front_result = self.cut_front.apply(inner_front, outer_left, outer_right, shape_3d_amount_front)
        cut_back_result = self.cut_back.apply(inner_back, outer_left, outer_right, shape_3d_amount_back)

        panel_left = outer_left.get(cut_front_result.index_left, cut_back_result.index_left).fix_errors()
        panel_back = cut_back_result.curve.copy()
        panel_right = outer_right.get(cut_back_result.index_right, cut_front_result.index_right).fix_errors()
        panel_front = cut_front_result.curve.copy()

        # spitzer schnitt
        # rechts
        # TODO: FIX!
        # if cut_front_result.index_right >= cut_back_result.index_right:
        #     panel_right = euklid.vector.PolyLine2D([])

        #     _cuts = panel_front.cut_with_polyline(panel_back, startpoint=len(panel_front) - 1)
        #     try:
        #         ik_front, ik_back = next(_cuts)
        #         panel_back = panel_back.get(0, ik_back)
        #         panel_front = panel_front.get(0, ik_front)
        #     except StopIteration:
        #         pass  # todo: fix!!

        # # lechts
        # if cut_front_result.index_left >= cut_back_result.index_left:
        #     panel_left = euklid.vector.PolyLine2D([])

        #     _cuts = panel_front.cut_with_polyline(panel_back, startpoint=0)
        #     try:
        #         ik_front, ik_back = next(_cuts)
        #         panel_back = panel_back.get(ik_back, len(panel_back)-1)
        #         panel_front = panel_front[ik_front, len(panel_back)-1]
        #     except StopIteration:
        #         pass  # todo: fix as well!

        panel_back = panel_back.get(len(panel_back)-1, 0)
        if panel_right:
            panel_right = panel_right.reverse()


        envelope = panel_right + panel_back
        if len(panel_left) > 0:
            envelope += panel_left.reverse()
        envelope += panel_front
        envelope += euklid.vector.PolyLine2D([envelope.nodes[0]])

        plotpart.layers["envelope"].append(envelope)

        if self.config.debug:
            plotpart.layers["debug"].append(euklid.vector.PolyLine2D([line.get(ik) for line, ik in inner_front]))
            plotpart.layers["debug"].append(euklid.vector.PolyLine2D([line.get(ik) for line, ik in inner_back]))
            for front, back in zip(inner_front, inner_back):
                plotpart.layers["debug"].append(front[0].get(front[1], back[1]))

        # sewings
        plotpart.layers["stitches"] += [
            self.inner[0].get(cut_front_result.inner_indices[0], cut_back_result.inner_indices[0]),
            self.inner[-1].get(cut_front_result.inner_indices[-1], cut_back_result.inner_indices[-1])
            ]

        # folding line
        self.front_curve = euklid.vector.PolyLine2D([
                line.get(x) for line, x in zip(self.inner, cut_front_result.inner_indices)
            ])
        self.back_curve = euklid.vector.PolyLine2D([
                line.get(x) for line, x in zip(self.inner, cut_back_result.inner_indices)
            ])

        plotpart.layers["marks"] += [
            self.front_curve,
            self.back_curve
        ]

        # TODO
        if False:
            if panel_right:
                right = euklid.vector.PolyLine2D([panel_front.last()]) + panel_right + euklid.vector.PolyLine2D([panel_back[0]])
                plotpart.layers["cuts"].append(right)

            plotpart.layers["cuts"].append(panel_back)

            if panel_left:
                left = euklid.vector.PolyLine2D([panel_back.last()]) + panel_left + euklid.vector.PolyLine2D([panel_front[0]])
                plotpart.layers["cuts"].append(left)

            plotpart.layers["cuts"].append(panel_front)
        else:
            plotpart.layers["cuts"].append(envelope.copy())

        self._insert_text(plotpart)
        self._insert_controlpoints(plotpart)
        self._insert_attachment_points(plotpart, attachment_points=attachment_points)
        self._insert_diagonals(plotpart)
        self._insert_rigidfoils(plotpart)
        #self._insert_center_rods(plotpart)
        # TODO: add in parametric way

        self._align_upright(plotpart)

        self.plotpart = plotpart
        return plotpart

    def get_material_usage(self):
        part = self.flatten([])
        envelope = part.layers["envelope"].polylines[0]
        area = envelope.get_area()

        return MaterialUsage().consume(self.panel.material, area)


    def get_point(self, x):
        ik = get_x_value(self.x_values, x)
        return [lst.get(ik) for lst in self.ballooned]

    def get_p1_p2(self, x, is_right):
        if is_right:
            front, back = self.panel.cut_front.x_right, self.panel.cut_back.x_right
        else:
            front, back = self.panel.cut_front.x_left, self.panel.cut_back.x_left

        if front <= x <= back:
            ik = get_x_value(self.x_values, x)

            p1 = self.ballooned[is_right].get(ik)
            p2 = self.outer_orig[is_right].get(ik)

            return p1, p2
        
        raise ValueError(f"not in range")

    def insert_mark(self, mark, x, layer: List, is_right):
        if mark is None:
            return

        if is_right:
            side = "right"
        else:
            side = "left"

        if getattr(self.panel.cut_front, f"x_{side}") <= x <= getattr(self.panel.cut_back, f"x_{side}"):
            ik = get_x_value(self.x_values, x)
            p1 = self.ballooned[is_right].get(ik)
            p2 = self.outer_orig[is_right].get(ik)

            layer += mark(p1, p2)

    def _align_upright(self, plotpart):
        ik_front = self.front_curve.walk(0, self.front_curve.get_length()/2)
        ik_back = self.back_curve.walk(0, self.back_curve.get_length()/2)

        p1 = self.front_curve.get(ik_front)
        p2 = self.back_curve.get(ik_back)
        
        vector = p2-p1

        angle = vector.angle() - math.pi/2

        plotpart.rotate(-angle)
        return plotpart

    def _insert_text(self, plotpart):
        text = self.panel.name
        text_width = self.config.allowance_design * 0.8 * len(text)

        if self.config.layout_seperate_panels and not self.panel.is_lower():
            curve = self.panel.cut_back.get_curve_2d(self.cell, self.config.midribs, exact=True)
        else:
            curve = self.panel.cut_front.get_curve_2d(self.cell, self.config.midribs, exact=True).reverse()

        ik_p1 = curve.walk(0, curve.get_length()*0.15)

        p1 = curve.get(ik_p1)
        ik_p2 = curve.walk(ik_p1, text_width)
        p2 = curve.get(ik_p2)
        align = "left"

        part_text = Text(text, p1, p2,
                         align=align,
                         valign=-0.9,
                         height=0.8)
        plotpart.layers["text"] += part_text.get_vectors()

    def _insert_controlpoints(self, plotpart):
        # insert chord-wise controlpoints
        layer = plotpart.layers["L0"]

        for x in self.config.distribution_controlpoints:
            self.insert_mark(self.config.marks_controlpoint, x, layer, False)
            self.insert_mark(self.config.marks_controlpoint, x, layer, True)
        
        # insert horizontal (spanwise) controlpoints
        x_dots = 2

        front = (
            self.front_curve,
            self.front_curve.offset(-self.cut_front.amount)
        )

        back = (
            self.back_curve,
            self.back_curve.offset(-self.cut_back.amount)
        )

        for i in range(x_dots):
            x = (i+1)/(x_dots+1)

            for inner, outer in (front, back):
                p1 = inner.get(inner.walk(0, inner.get_length() * x))
                p2 = outer.get(outer.walk(0, outer.get_length() * x))
                plotpart.layers["L0"] += self.config.marks_controlpoint(p1, p2)


    def _insert_diagonals(self, plotpart):
        layer = plotpart.layers["L0"]


        for strap in self.cell.straps + self.cell.diagonals:
            strap: DiagonalRib

            is_upper = strap.left.is_upper and strap.right.is_upper
            is_lower = strap.left.is_lower and strap.right.is_lower

            if is_upper or is_lower:
                factor = 1
                if is_upper:
                    factor = -1

                self.insert_mark(self.config.marks_diagonal_center, factor * strap.left.center, layer, False)
                self.insert_mark(self.config.marks_diagonal_center, factor * strap.right.center, layer, True)

                # more than 25cm? -> add start / end marks too
                if strap.left.get_curve(self.cell.rib1).get_length() > 0.25:
                    self.insert_mark(self.config.marks_diagonal_front, factor * strap.left.start_x, layer, False)
                    self.insert_mark(self.config.marks_diagonal_back, factor * strap.left.end_x, layer, False)

                if strap.right.get_curve(self.cell.rib1).get_length() > 0.25:
                    self.insert_mark(self.config.marks_diagonal_back, factor * strap.right.start_x, layer, True)
                    self.insert_mark(self.config.marks_diagonal_front, factor * strap.right.end_x, layer, True)

            else:
                if strap.left.is_lower:
                    self.insert_mark(self.config.marks_diagonal_center, strap.left.center, layer, False)
                
                if strap.right.is_lower:
                    self.insert_mark(self.config.marks_diagonal_center, strap.right.center, layer, True)

    def _insert_attachment_points(self, plotpart, attachment_points):
        def insert_side_mark(name, positions, is_right):
            try:
                p1, p2 = self.get_p1_p2(positions[0], is_right)
                diff = p1 - p2
                if is_right:
                    start = p1 + diff
                    end = start + diff
                else:
                    end = p1 + diff
                    start = end + diff                   


                text_align = "left" if is_right else "right"
                plotpart.layers["text"] += Text(attachment_point.name, start, end,
                                                            size=0.01,  # 1cm
                                                            align=text_align, valign=0, height=0.8).get_vectors()
            except  ValueError:
                pass

            for position in positions:
                self.insert_mark(self.config.marks_attachment_point, position, plotpart.layers["marks"], is_right)
                self.insert_mark(self.config.marks_laser_attachment_point, position, plotpart.layers["L0"], is_right)

        for attachment_point in self.cell.rib1.attachment_points:
            # left side
            positions = attachment_point.get_x_values(self.cell.rib1)
            insert_side_mark(attachment_point.name, positions, False)

        for attachment_point in self.cell.rib2.attachment_points:
            # left side
            positions = attachment_point.get_x_values(self.cell.rib2)
            insert_side_mark(attachment_point.name, positions, True)
        
        for attachment_point in self.cell.attachment_points:

            cell_pos = attachment_point.cell_pos

            cut_f_l = self.panel.cut_front.x_left
            cut_f_r = self.panel.cut_front.x_right
            cut_b_l = self.panel.cut_back.x_left
            cut_b_r = self.panel.cut_back.x_right
            cut_f = cut_f_l + cell_pos * (cut_f_r - cut_f_l)
            cut_b = cut_b_l + cell_pos * (cut_b_r - cut_b_l)

            positions = [attachment_point.rib_pos]
            
            for rib_pos_no, rib_pos in enumerate(positions):

                if cut_f <= attachment_point.rib_pos <= cut_b:
                    left, right = self.get_point(rib_pos)

                    p1 = left + (right - left) * cell_pos
                    d = (right - left).normalized() * 0.008 # 8mm
                    if cell_pos == 1:
                        p2 = p1 + d
                    else:
                        p2 = p1 - d
                        
                    if cell_pos in (1, 0):
                        x1, x2 = self.get_p1_p2(rib_pos, cell_pos)
                        plotpart.layers["marks"] += self.config.marks_attachment_point(x1, x2)
                        plotpart.layers["L0"] += self.config.marks_laser_attachment_point(x1, x2)
                    else:
                        plotpart.layers["marks"] += self.config.marks_attachment_point(p1, p2)
                        plotpart.layers["L0"] += self.config.marks_laser_attachment_point(p1, p2)
                    
                    if self.config.insert_attachment_point_text and rib_pos_no == 0:
                        text_align = "left" if cell_pos > 0.7 else "right"

                        if text_align == "right":
                            d1 = (self.get_point(cut_f_l)[0] - left).length()
                            d2 = ((self.get_point(cut_b_l)[0] - left)).length()
                        else:
                            d1 = ((self.get_point(cut_f_r)[1] - right)).length()
                            d2 = ((self.get_point(cut_b_r)[1] - right)).length()

                        bl = self.ballooned[0]
                        br = self.ballooned[1]

                        text_height = 0.01 * 0.8
                        dmin = text_height + 0.001

                        if d1 < dmin and d2 + d1 > 2*dmin:
                            offset = dmin - d1
                            ik = get_x_value(self.x_values, rib_pos)
                            left = bl.get(bl.walk(ik, offset))
                            right = br.get(br.walk(ik, offset))
                        elif d2 < dmin and d1 + d2 > 2*dmin:
                            offset = dmin - d2
                            ik = get_x_value(self.x_values, rib_pos)
                            left = bl.get(bl.walk(ik, -offset))
                            right = br.get(br.walk(ik, -offset))

                        if self.config.layout_seperate_panels and self.panel.is_lower:
                            # rotated later
                            p2 = left
                            p1 = right
                            # text_align = text_align
                        else:
                            p1 = left
                            p2 = right
                            # text_align = text_align
                        plotpart.layers["text"] += Text(" {} ".format(attachment_point.name), p1, p2,
                                                        size=0.01,  # 1cm
                                                        align=text_align, valign=0, height=0.8).get_vectors()
    
    def _insert_rigidfoils(self, plotpart):
        for rigidfoil in self.cell.rigidfoils:
            line = rigidfoil.draw_panel_marks(self.cell, self.panel)
            if line is not None:
                plotpart.layers["marks"].append(line)

                # laser dots
                plotpart.layers["L0"].append(euklid.vector.PolyLine2D([line.get(0)]))
                plotpart.layers["L0"].append(euklid.vector.PolyLine2D([line.get(len(line)-1)]))



class CellPlotMaker:
    run_check = True
    DefaultConf = PatternConfig
    DribPlot = DribPlot
    StrapPlot = StrapPlot
    PanelPlot = PanelPlot

    def __init__(self, cell: Cell, attachment_points: List[AttachmentPoint], config: Optional[Config]=None):
        self.cell = cell
        self.attachment_points = attachment_points
        self.config = self.DefaultConf(config)
        
        self.consumption = MaterialUsage()

        self._flattened_cell = None

    def _get_flatten_cell(self):
        if self._flattened_cell is None:
            flattened_cell = self.cell.get_flattened_cell(self.config.midribs)

            left_bal, right_bal = flattened_cell["ballooned"]

            outer_left = left_bal.offset(-self.config.allowance_general)
            outer_right = right_bal.offset(self.config.allowance_general)

            outer_orig = [
                left_bal.offset(-self.config.allowance_general, simple=True),
                right_bal.offset(self.config.allowance_general, simple=True),
            ]

            outer = [l.fix_errors() for l in [outer_left, outer_right]]

            flattened_cell["outer"] = outer
            flattened_cell["outer_orig"] = outer_orig

            self._flattened_cell = flattened_cell

        return self._flattened_cell

    def get_panels(self, panels: Optional[List[Panel]]=None) -> List[PlotPart]:
        cell_panels = []
        flattened_cell = self._get_flatten_cell()
        self.cell.calculate_3d_shaping(numribs=self.config.midribs)

        if panels is None:
            panels = self.cell.panels

        for panel in panels:
            plot = self.PanelPlot(panel, self.cell, flattened_cell, self.config)
            dwg = plot.flatten(self.attachment_points)
            cell_panels.append(dwg)
            self.consumption += plot.get_material_usage()
        
        return cell_panels

    def get_panels_lower(self) -> List[PlotPart]:
        panels = [p for p in self.cell.panels if p.is_lower()]
        return self.get_panels(panels)

    def get_panels_upper(self) -> List[PlotPart]:
        panels = [p for p in self.cell.panels if not p.is_lower()]
        return self.get_panels(panels)

    def get_dribs(self) -> list[PlotPart]:
        diagonals = self.cell.diagonals[:]
        diagonals.sort(key=lambda d: d.name)
        dribs = []
        for drib in diagonals[::-1]:
            drib_plot = self.DribPlot(drib, self.cell, self.config)
            dribs.append(drib_plot.flatten(self.attachment_points))
            self.consumption += drib_plot.get_material_usage()
        
        return dribs

    def get_straps(self) -> List[PlotPart]:
        straps = self.cell.straps[:]
        straps.sort(key=lambda d: d.name)
        result = []
        for strap in straps:
            plot = self.StrapPlot(strap, self.cell, self.config)
            result.append(plot.flatten(self.attachment_points))
            self.consumption += plot.get_material_usage()
        
        return result
    
    def get_rigidfoils(self) -> List[PlotPart]:
        rigidfoils = []
        for rigidfoil in self.cell.rigidfoils:
            rigidfoils.append(rigidfoil.get_flattened(self.cell))
        
        return rigidfoils
