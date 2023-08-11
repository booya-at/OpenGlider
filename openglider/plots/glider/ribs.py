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



if TYPE_CHECKING:
    from openglider.glider.rib import Rib
    from openglider.glider import Glider


Vector2D = euklid.vector.Vector2D

logger = logging.getLogger(__name__)


class RigidFoilPlot:
    rigidfoil: RigidFoilBase
    ribplot: RibPlot

    inner_curve: euklid.vector.PolyLine2D | None = None
    outer_curve: euklid.vector.PolyLine2D | None = None

    def __init__(self, rigidfoil: RigidFoilBase, ribplot: RibPlot) -> None:
        self.rigidfoil = rigidfoil
        self.ribplot = ribplot

    def add_text(self, plotpart: PlotPart) -> None:
        (_, p1), (_, p2) = self.get_cap(-1, True)

        plotpart.layers[self.ribplot.layer_name_text] += Text(
            self.rigidfoil.name, p1, p2, align="center", valign=0.6
        ).get_vectors()

    def get_cap(self, position: int, rear: bool) -> tuple[tuple[Vector2D, Vector2D], tuple[Vector2D, Vector2D]]:
        assert self.inner_curve is not None and self.outer_curve is not None

        # back cap
        p1 = self.inner_curve.nodes[position]
        p2 = self.outer_curve.nodes[position]
        angle = math.pi/2
        if rear:
            angle = -angle
        diff = euklid.vector.Rotation2D(angle).apply(p1-p2).normalized() * self.rigidfoil.cap_length.si

        return (
            (p1, p2),
            (p1+diff, p2+diff)
        )
    
    def _get_inner_outer(self, glider: Glider) -> tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]:
        curve = self.rigidfoil.get_flattened(self.ribplot.rib, glider)

        distance = self.ribplot.rib.convert_to_chordlength(self.rigidfoil.distance)
        d_outer = self.ribplot.config.allowance_general + distance.si

        inner_curve = curve.offset(-self.ribplot.config.allowance_general).fix_errors()
        outer_curve = curve.offset(d_outer).fix_errors()

        return inner_curve, outer_curve
    
    def flatten(self, glider: Glider) -> PlotPart:
        plotpart = PlotPart()

        controlpoints: list[tuple[float, list[euklid.vector.PolyLine2D]]] = []
        for x in self.ribplot.config.get_controlpoints(self.ribplot.rib):
            for mark in self.ribplot.insert_mark(x, self.ribplot.config.marks_controlpoint, insert=False):
                controlpoints.append((x, mark))

        curve = self.rigidfoil.get_flattened(self.ribplot.rib, glider)

        # add marks into the profile
        self.ribplot.plotpart.layers[self.ribplot.layer_name_rigidfoils].append(curve)
        self.ribplot.plotpart.layers[self.ribplot.layer_name_laser_dots].append(euklid.vector.PolyLine2D([curve.get(0)]))
        self.ribplot.plotpart.layers[self.ribplot.layer_name_laser_dots].append(euklid.vector.PolyLine2D([curve.get(len(curve)-1)]))

        self.inner_curve, self.outer_curve = self._get_inner_outer(glider)

        plotpart.layers[self.ribplot.layer_name_marks].append(curve)

        back_cap = self.get_cap(-1, True)
        plotpart.layers[self.ribplot.layer_name_marks].append(euklid.vector.PolyLine2D(list(back_cap[0])))

        front_cap = self.get_cap(0, False)
        plotpart.layers[self.ribplot.layer_name_marks].append(euklid.vector.PolyLine2D(list(front_cap[0])))
        
        outline = self.inner_curve
        outline += euklid.vector.PolyLine2D(list(back_cap[1]))
        outline += self.outer_curve.reverse()
        outline += euklid.vector.PolyLine2D(list(front_cap[1])).reverse()

        for x, controlpoint in controlpoints:
            p = controlpoint[0].nodes[0]
            fits_x = self.rigidfoil.start < x and x < self.rigidfoil.end
            if fits_x or outline.contains(p):
                plotpart.layers[self.ribplot.layer_name_laser_dots] += controlpoint
                
        plotpart.layers[self.ribplot.layer_name_outline].append(outline.fix_errors().close())

        self.add_text(plotpart)

        return plotpart



class RibPlot:
    x_values: list[float]
    inner: euklid.vector.PolyLine2D
    outer: euklid.vector.PolyLine2D

    config: PatternConfig
    DefaultConf = PatternConfig
    RigidFoilPlotFactory = RigidFoilPlot

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


class SingleSkinRibPlot(RibPlot):
    skin_cut: Percentage | None = None

    def _get_inner_outer(self, x_value: Percentage | float) -> tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        # TODO: shift when after the endpoint

        if self.skin_cut is None or x_value < self.skin_cut:
            return super()._get_inner_outer(x_value)
        else:
            hull = self.rib.get_hull()
            segments = hull.curve.get_segments()
            ik = hull.get_ik(x_value)

            segment = segments[min(int(ik), len(segments)-1)].normalized()
            normal = euklid.vector.Rotation2D(math.pi/2).apply(segment)


            p1 = hull.curve.get(ik) * self.rib.chord
            p2 = p1 + normal * self.config.allowance_general
            return p1, p2
        
    def insert_controlpoints(self, controlpoints: list[float]=None) -> None:
        if self.skin_cut is not None:
            controlpoints = [x for x in self.config.get_controlpoints(self.rib) if x < self.skin_cut.si]

        return super().insert_controlpoints(controlpoints)

    def _get_singleskin_cut(self, glider: Glider) -> Percentage:
        if self.skin_cut is None:
            singleskin_cut = None

            for cell in glider.cells:
                # only a back cut can be a singleskin_cut
                # asserts there is only one removed singleskin Panel!
                # maybe asserts no singleskin rib on stabilo
                if cell.rib1 == self.rib:
                    for panel in cell.panels:
                        if panel.cut_back.cut_type == PANELCUT_TYPES.singleskin:
                            singleskin_cut = panel.cut_back.x_left
                            break
                if cell.rib2 == self.rib:
                    for panel in cell.panels:
                        if panel.cut_back.cut_type == PANELCUT_TYPES.singleskin:
                            singleskin_cut = panel.cut_back.x_right
                            break
            
            if singleskin_cut is None:
                raise ValueError(f"no singleskin cut found for rib: {self.rib.name}")

            self.skin_cut = singleskin_cut

        return self.skin_cut

    def flatten(self, glider: Glider, add_rigidfoils_to_plot: bool=True) -> PlotPart:
        self._get_singleskin_cut(glider)
        return super().flatten(glider, add_rigidfoils_to_plot=add_rigidfoils_to_plot)

    def draw_outline(self, glider: Glider) -> euklid.vector.PolyLine2D:
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer
        inner_rib = self.inner
        t_e_allowance = self.config.allowance_trailing_edge
        p1 = inner_rib.get(0) + euklid.vector.Vector2D([0, 1])
        p2 = inner_rib.get(0) + euklid.vector.Vector2D([0, -1])
        cuts = outer_rib.cut(p1, p2)

        start = cuts[0][0]

        contour = euklid.vector.PolyLine2D([])

        # outer is going from the back back until the singleskin cut

        singleskin_cut_left = self._get_singleskin_cut(glider)
        single_skin_cut = self.rib.profile_2d(singleskin_cut_left)

        buerzl = euklid.vector.PolyLine2D([
            inner_rib.get(0),
            inner_rib.get(0) + euklid.vector.Vector2D([t_e_allowance, 0]),
            outer_rib.get(start) + euklid.vector.Vector2D([t_e_allowance, 0]),
            outer_rib.get(start)
            ])
        contour += outer_rib.get(start, single_skin_cut)
        contour += inner_rib.get(single_skin_cut, len(inner_rib)-1)
        contour += buerzl

        
        return contour
