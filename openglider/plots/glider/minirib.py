from __future__ import annotations

import math
from typing import TYPE_CHECKING
from collections.abc import Callable

import euklid
from openglider import logging
from openglider.airfoil import get_x_value
from openglider.glider.cell.diagonals import (DiagonalRib, DiagonalSide,
                                              TensionStrap)
from openglider.glider.cell.panel import PANELCUT_TYPES
from openglider.glider.rib.rigidfoils import RigidFoilBase
from openglider.plots.config import PatternConfig
from openglider.plots.usage_stats import MaterialUsage
from openglider.utils.config import Config
from openglider.vector.drawing import PlotPart
from openglider.vector.text import Text
from openglider.vector.unit import Percentage
from openglider.glider.rib import MiniRib
from openglider.plots.usage_stats import Material, MaterialUsage




if TYPE_CHECKING:
    from openglider.glider.rib import Rib
    from openglider.glider.cell import Cell
    from openglider.glider import Glider


Vector2D = euklid.vector.Vector2D

logger = logging.getLogger(__name__)


class MiniRibPlot:
    minirib: MiniRib
    ribplot: RibPlot
    cell: Cell

    config: PatternConfig
    DefaultConf = PatternConfig

    layer_name_outline = "cuts"
    layer_name_sewing = "sewing"
    layer_name_rigidfoils = "marks"
    layer_name_text = "text"
    layer_name_marks = "marks"
    layer_name_laser_dots = "L0"
    layer_name_crossports = "cuts"


    outer_curve: euklid.vector.PolyLine2D | None = None
    

    def __init__(self, minirib: MiniRib, cell :Cell, config: Config | None=None) -> None:
        self.minirib = minirib
        #self.ribplot = ribplot
        self.cell = cell
        self.config = self.DefaultConf(config)


    def get_point(self, x: float | Percentage, y: float=-1.) -> euklid.vector.Vector2D:
        x = float(x)
        assert x >= 0

        profile = self.minirib.get_3d(self.cell).flatten()

        p = profile.profilepoint(x, y)
        return p * profile.curve.nodes[0][0]


    def add_text(self, plotpart: PlotPart) -> None:
        
        posX = 0.85 #self.minirib.front_cut +0.05

        p1 = self.get_point(posX, -1)
        p2 = self.get_point(posX, 1)

        _text = Text(self.minirib.name, p1, p2, size=0.01, align="center", valign= 0)


        plotpart.layers[self.layer_name_text] += _text.get_vectors()

    
    def draw_outline(self) -> euklid.vector.PolyLine2D:
        """
        Cut trailing edge of outer rib
        """
        outer_minirib = self.outer.fix_errors()
        inner_minirib = self.inner
        t_e_allowance = self.config.allowance_trailing_edge
        p1 = inner_minirib.nodes[0] + euklid.vector.Vector2D([0, 1])
        p2 = inner_minirib.nodes[0] + euklid.vector.Vector2D([0, -1])


        p3 = euklid.vector.Vector2D([min(x[0] for x in inner_minirib.tolist()), max(x[1] for x in inner_minirib.tolist())]) # probably there is a euklid function for that,... 
        p4 = euklid.vector.Vector2D([min(x[0] for x in inner_minirib.tolist()), min(x[1] for x in inner_minirib.tolist())])

        cuts = outer_minirib.cut(p1, p2)

        front_cuts = outer_minirib.cut(p3, p4)

        if len(cuts) != 2:
            raise Exception("could not cut minirib airfoil TE")

        start = cuts[0][0]
        stop = cuts[1][0]

        middle_top = front_cuts[0][0]
        middle_bot = front_cuts[1][0]

        buerzl = [
            outer_minirib.get(stop),
            outer_minirib.get(stop) + euklid.vector.Vector2D([t_e_allowance, 0]),
            outer_minirib.get(start) + euklid.vector.Vector2D([t_e_allowance, 0]),
            outer_minirib.get(start)
            ]

        #no sewing allowance front
        nosew = [
            outer_minirib.get(middle_top),
            outer_minirib.get(middle_bot)
            ]

        contour = euklid.vector.PolyLine2D(
             outer_minirib.get(start, middle_top).nodes + nosew + outer_minirib.get(middle_bot, stop).nodes + buerzl
        )

        return contour
    
    def get_material_usage(self) -> MaterialUsage:
        dwg = self.plotpart

        curves = dwg.layers["envelope"].polylines
        usage = MaterialUsage()
        material = Material(weight=38, name="mribs")

        if curves:
            area = curves[0].get_area()

        #to do implement holes for miniribs
        #
        #    for curve in self.mrib.get_holes(self.cell)[0]:
        #        area -= curve.get_area()
        #        
            usage.consume(material, area)

        return usage
    
    
    def flatten(self) -> PlotPart:
        plotpart = PlotPart()

        #controlpoints: list[tuple[float, list[euklid.vector.PolyLine2D]]] = []
        #for x in self.ribplot.config.get_controlpoints(self.ribplot.rib):
        #    for mark in self.ribplot.insert_mark(x, self.ribplot.config.marks_controlpoint, insert=False):
        #        controlpoints.append((x, mark))

        self.inner = self.minirib.get_flattened(self.cell)
        self.outer = self.inner.offset(self.config.allowance_general, simple=False)
        
        # insert cut
        envelope = self.draw_outline()


        curve = self.inner
        # add marks into the profile
        #self.ribplot.plotpart.layers[self.ribplot.layer_name_minirib].append(curve)
        #self.ribplot.plotpart.layers[self.ribplot.layer_name_laser_dots].append(euklid.vector.PolyLine2D([curve.get(0)]))
        #self.ribplot.plotpart.layers[self.ribplot.layer_name_laser_dots].append(euklid.vector.PolyLine2D([curve.get(len(curve)-1)]))

        #self.inner_curve, self.outer_curve = self._get_inner_outer(glider)

        plotpart.layers[self.layer_name_sewing].append(self.inner)

        
        
        
        #outline += euklid.vector.PolyLine2D(list(back_cap[1]))
        #outline += self.outer_curve.reverse()
        #outline += euklid.vector.PolyLine2D(list(front_cap[1])).reverse()

        #for x, controlpoint in controlpoints:
        #    p = controlpoint[0].nodes[0]
        #    fits_x = self.rigidfoil.start < x and x < self.rigidfoil.end
        #    if fits_x or outline.contains(p):
        #        plotpart.layers[self.ribplot.layer_name_laser_dots] += controlpoint
                
        plotpart.layers[self.layer_name_outline].append(envelope)

        self.add_text(plotpart)

        self.plotpart = plotpart

        return plotpart



class RibPlot:
    x_values: list[float]
    inner: euklid.vector.PolyLine2D
    outer: euklid.vector.PolyLine2D

    config: PatternConfig
    DefaultConf = PatternConfig

    MiniRibPlotFactory = MiniRibPlot


    rib: Rib

    layer_name_outline = "cuts"
    layer_name_sewing = "sewing"
    layer_name_rigidfoils = "marks"
    layer_name_text = "text"
    layer_name_marks = "marks"
    layer_name_laser_dots = "L0"
    layer_name_crossports = "cuts"

    def __init__(self, rib: Rib, config: Config | None=None):
        self.rib = rib
        self.config = self.DefaultConf(config)

        #self.plotpart = self.x_values = self.inner = self.outer = None

    def flatten(self, glider: Glider, add_rigidfoils_to_plot: bool=True) -> PlotPart:
        self.plotpart = PlotPart(name=self.rib.name, material_code=str(self.rib.material))
        prof2d = self.rib.get_hull()

        self.x_values = prof2d.x_values
        self.inner = prof2d.curve.scale(self.rib.chord)
        self.inner_normals = self.inner.normvectors()
        self.outer = self.inner.offset(self.config.allowance_general, simple=False)

        self._insert_attachment_points(glider)
        holes = self.insert_holes()

        panel_cuts: set[Percentage] = set()
        for cell in glider.cells:
            if self.config.insert_design_cuts:
                panels = cell.panels
            else:
                panels = cell.get_connected_panels()
            if cell.rib1 == self.rib:
                # panel-cuts
                for panel in panels:
                    panel_cuts.add(panel.cut_front.x_left)
                    panel_cuts.add(panel.cut_back.x_left)

                # diagonals
                all_diagonals: list[DiagonalRib | TensionStrap] = cell.diagonals + cell.straps  # type: ignore
                for diagonal in all_diagonals:
                    self.insert_drib_mark(diagonal.left)

            elif cell.rib2 == self.rib:
                for panel in panels:
                    panel_cuts.add(panel.cut_front.x_right)
                    panel_cuts.add(panel.cut_back.x_right)

                for diagonal in cell.diagonals + cell.straps:  # type: ignore
                    self.insert_drib_mark(diagonal.right)

        for cut in panel_cuts:
            if -0.99 < cut.si and cut.si < 0.99:
                self.insert_mark(cut, self.config.marks_panel_cut)

        self._insert_text(self.rib.name)
        self.insert_controlpoints()

        # insert cut
        envelope = self.draw_outline(glider)

        area = envelope.get_area()
        for hole in holes:
            area -= hole.get_area()

        self.weight = MaterialUsage().consume(self.rib.material, area)

        self.plotpart.layers[self.layer_name_outline] += [envelope]
        self.plotpart.layers[self.layer_name_sewing].append(self.inner)

        rigidfoils = self.draw_rigidfoils(glider)
        if add_rigidfoils_to_plot and rigidfoils:
            diff = max([r.max_x for r in rigidfoils])
            for rigidfoil in rigidfoils:
                rigidfoil.move(euklid.vector.Vector2D([-(diff-self.plotpart.min_x+0.2), 0]))

                self.plotpart += rigidfoil

        return self.plotpart

    def _get_inner_outer(self, x_value: Percentage | float) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        ik = get_x_value(self.x_values, x_value)

        #ik = get_x_value(self.x_values, position)
        inner = self.inner.get(ik)
        outer = inner + self.inner_normals.get(ik) * self.config.allowance_general
        #inner = self.inner[ik]
        # outer = self.outer[ik]
        return inner, outer

    def insert_mark(
        self,
        position: float | Percentage,
        mark_function: Callable[[euklid.vector.Vector2D, euklid.vector.Vector2D], dict[str, list[euklid.vector.PolyLine2D]]],
        insert: bool=True
        ) -> list[list[euklid.vector.PolyLine2D]]:

        marks = []
        #if mark_function_func := getattr(mark_function, "__func__", None):
        #    mark_function = mark_function_func

        if mark_function is None:
            return

        inner, outer = self._get_inner_outer(position)

        for mark_layer, mark in mark_function(inner, outer).items():
            if insert:
                self.plotpart.layers[mark_layer] += mark

            marks.append(mark)
        
        return marks

    def insert_controlpoints(self, controlpoints: list[float]=None) -> None:
        if controlpoints is None:
            controlpoints = list(self.config.get_controlpoints(self.rib))
        for x in controlpoints:
            self.insert_mark(x, self.config.marks_controlpoint)

    def get_point(self, x: float | Percentage, y: float=-1.) -> euklid.vector.Vector2D:
        x = float(x)
        assert x >= 0
        p = self.rib.profile_2d.profilepoint(x, y)
        return p * self.rib.chord

    def insert_drib_mark(self, side: DiagonalSide) -> None:        
        if side.is_lower:
            return  # disabled
            self.insert_mark(side.start_x, self.config.marks_diagonal_front)
            self.insert_mark(side.end_x, self.config.marks_diagonal_back)
        elif side.is_upper:
            self.insert_mark(-side.start_x(self.rib), self.config.marks_diagonal_back)
            self.insert_mark(-side.end_x(self.rib), self.config.marks_diagonal_front)
        else:
            p1 = self.get_point(side.start_x(self.rib), side.height)
            p2 = self.get_point(side.end_x(self.rib), side.height)
            self.plotpart.layers[self.layer_name_marks].append(euklid.vector.PolyLine2D([p1, p2]))

    def insert_holes(self) -> list[euklid.vector.PolyLine2D]:
        holes: list[PlotPart] = []
        for hole in self.rib.holes:            
            holes.append(hole.get_flattened(self.rib, num=200, layer_name=self.layer_name_crossports))
        
        curves: list[euklid.vector.PolyLine2D] = []
        for plotpart in holes:
            self.plotpart += plotpart
            curves += list(plotpart.layers["cuts"])

        return curves

    def draw_outline(self, glider: Glider) -> euklid.vector.PolyLine2D:
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer.fix_errors()
        inner_rib = self.inner
        t_e_allowance = self.config.allowance_trailing_edge
        p1 = inner_rib.nodes[0] + euklid.vector.Vector2D([0, 1])
        p2 = inner_rib.nodes[0] + euklid.vector.Vector2D([0, -1])
        cuts = outer_rib.cut(p1, p2)

        if len(cuts) != 2:
            raise Exception("could not cut airfoil TE")

        start = cuts[0][0]
        stop = cuts[1][0]

        buerzl = [
            outer_rib.get(stop),
            outer_rib.get(stop) + euklid.vector.Vector2D([t_e_allowance, 0]),
            outer_rib.get(start) + euklid.vector.Vector2D([t_e_allowance, 0]),
            outer_rib.get(start)
            ]

        contour = euklid.vector.PolyLine2D(
            outer_rib.get(start, stop).nodes + buerzl
        )

        return contour
    
    def walk(self, x: float, amount: float) -> float:
        ik = get_x_value(self.x_values, x)

        ik_new = self.inner.walk(ik, amount)

        return self.inner.get(ik_new)[0]/self.rib.chord
        

    def _insert_attachment_points(self, glider: Glider) -> None:
        for attachment_point in self.rib.attachment_points:
            positions = attachment_point.get_x_values(self.rib)

            for position in positions:
                self.insert_mark(position, self.config.marks_attachment_point)

    def _insert_text(self, text: str) -> None:
        if self.config.rib_text_in_seam:
            inner, outer = self._get_inner_outer(self.config.rib_text_pos)
            diff = outer - inner

            p1 = inner + diff * 0.5
            p2 = p1 + euklid.vector.Rotation2D(-math.pi/2).apply(diff)

            _text = Text(text, p1, p2, size=(outer-inner).length()*0.5, valign=0)
            #_text = Text(text, p1, p2, size=0.05)
        else:
            p1 = self.get_point(0.05, -1)
            p2 = self.get_point(0.05, 1)

            _text = Text(text, p1, p2, size=0.01, align="center")


        self.plotpart.layers[self.layer_name_text] += _text.get_vectors()
    
    def draw_rigidfoils(self, glider: Glider) -> list[PlotPart]:
        result = []

        # rigidfoils
        for i, rigid in enumerate(self.rib.get_rigidfoils()):
            plt = self.RigidFoilPlotFactory(rigidfoil=rigid, ribplot=self)
            result.append(plt.flatten(glider))

        return result
