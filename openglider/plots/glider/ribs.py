from __future__ import annotations

import math
from typing import TYPE_CHECKING, Callable, List, Optional, Set, Tuple, Union

import euklid
import openglider.glider
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

if TYPE_CHECKING:
    from openglider.glider.rib import Rib
    from openglider.glider import Glider


logger = logging.getLogger(__name__)

class RibPlot(object):
    x_values: List[float]
    inner: euklid.vector.PolyLine2D
    outer: euklid.vector.PolyLine2D

    DefaultConf = PatternConfig

    rib: Rib

    layer_name_outline = "cuts"
    layer_name_sewing = "sewing"
    layer_name_rigidfoils = "marks"
    layer_name_text = "text"
    layer_name_marks = "marks"
    layer_name_laser_dots = "L0"
    layer_name_crossports = "cuts"

    def __init__(self, rib: Rib, config: Optional[Config]=None):
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

        panel_cuts: Set[float] = set()
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
                all_diagonals: List[Union[DiagonalRib, TensionStrap]] = cell.diagonals + cell.straps  # type: ignore
                for diagonal in all_diagonals:
                    self.insert_drib_mark(diagonal.left)

            elif cell.rib2 == self.rib:
                for panel in panels:
                    panel_cuts.add(panel.cut_front.x_right)
                    panel_cuts.add(panel.cut_back.x_right)

                for diagonal in cell.diagonals + cell.straps:  # type: ignore
                    self.insert_drib_mark(diagonal.right)

        for cut in panel_cuts:
            if cut not in (-1, 1):
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
        rigidfoils.move(euklid.vector.Vector2D([-(rigidfoils.max_x-self.plotpart.min_x+0.2), 0]))

        if add_rigidfoils_to_plot:
            self.plotpart += rigidfoils

        return self.plotpart

    def _get_inner_outer(self, x_value: float) -> Tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        ik = get_x_value(self.x_values, x_value)

        #ik = get_x_value(self.x_values, position)
        inner = self.inner.get(ik)
        outer = inner + self.inner_normals.get(ik) * self.config.allowance_general
        #inner = self.inner[ik]
        # outer = self.outer[ik]
        return inner, outer

    def insert_mark(
        self,
        position: float,
        mark_function: Callable[[euklid.vector.Vector2D, euklid.vector.Vector2D], List[euklid.vector.PolyLine2D]],
        laser: bool=False,
        insert: bool=True
        ) -> List[euklid.vector.PolyLine2D]:

        if mark_function_func := getattr(mark_function, "__func__", None):
            mark_function = mark_function_func

        if mark_function is None:
            return

        inner, outer = self._get_inner_outer(position)

        if laser:
            layer = self.layer_name_laser_dots
        else:
            layer = self.layer_name_marks

        mark = mark_function(inner, outer)
        if insert:
            self.plotpart.layers[layer] += mark
        return mark

    def insert_controlpoints(self) -> None:
        marks = []
        for x in self.config.distribution_controlpoints:
            marks.append(self.insert_mark(x, self.config.marks_controlpoint, laser=True))       
        

    def get_point(self, x: float, y: float=-1.) -> euklid.vector.Vector2D:
        assert x >= 0
        p = self.rib.profile_2d.profilepoint(x, y)
        return p * self.rib.chord

    def insert_drib_mark(self, side: DiagonalSide) -> None:        
        if side.is_lower:
            return  # disabled
            self.insert_mark(side.start_x, self.config.marks_diagonal_front)
            self.insert_mark(side.end_x, self.config.marks_diagonal_back)
            self.insert_mark(side.center, self.config.marks_diagonal_center, laser=True)
        elif side.is_upper:
            self.insert_mark(-side.start_x, self.config.marks_diagonal_back)
            self.insert_mark(-side.end_x, self.config.marks_diagonal_front)
            #self.insert_mark(-side.center, self.config.marks_diagonal_center, laser=True)
        else:
            p1 = self.get_point(side.start_x, side.start_height)
            p2 = self.get_point(side.end_x, side.end_height)
            self.plotpart.layers[self.layer_name_marks].append(euklid.vector.PolyLine2D([p1, p2]))

    def insert_holes(self) -> List[euklid.vector.PolyLine2D]:
        holes = []
        for hole in self.rib.holes:
            for l in hole.get_flattened(self.rib):
                self.plotpart.layers[self.layer_name_crossports].append(l)
                holes.append(l)
        
        return holes

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
                self.insert_mark(position, self.config.marks_laser_attachment_point, laser=True)

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
    
    def draw_rigidfoils(self, glider: Glider) -> PlotPart:
        plotpart = PlotPart()

        controlpoints = []
        for x in self.config.distribution_controlpoints:
            controlpoints.append(self.insert_mark(x, self.config.marks_controlpoint, laser=True, insert=False))

        def draw_rigid(rigidfoil: RigidFoilBase, name: str) -> None:
            curve = rigidfoil.get_flattened(self.rib, glider)

            # add marks into the profile
            self.plotpart.layers[self.layer_name_rigidfoils].append(curve)
            self.plotpart.layers[self.layer_name_laser_dots].append(euklid.vector.PolyLine2D([curve.get(0)]))
            self.plotpart.layers[self.layer_name_laser_dots].append(euklid.vector.PolyLine2D([curve.get(len(curve)-1)]))

            inner = curve.offset(-self.config.allowance_general).fix_errors()
            outer = curve.offset(self.config.allowance_general).fix_errors()

            plotpart.layers[self.layer_name_marks].append(curve)

            # back cap
            p1 = inner.nodes[-1]
            p2 = outer.nodes[-1]

            plotpart.layers[self.layer_name_marks].append(euklid.vector.PolyLine2D([p1, p2]))
            diff = euklid.vector.Rotation2D(-math.pi/2).apply(p1-p2).normalized() * 0.02
            back_cap = euklid.vector.PolyLine2D([
                p1 + diff,
                p2 + diff
            ])

            plotpart.layers[self.layer_name_text] += Text(
                name, p2, p2+diff, align="center", valign=0.6
            ).get_vectors()


            # front cap -> close to start
            p1 = inner.nodes[0]
            p2 = outer.nodes[0]

            plotpart.layers[self.layer_name_marks].append(euklid.vector.PolyLine2D([p1, p2]))
            diff = euklid.vector.Rotation2D(math.pi/2).apply(p1-p2).normalized() * 0.02
            front_cap = euklid.vector.PolyLine2D([
                p2 + diff,
                p1 + diff,
                p1
            ])




            # back cap

            outline = inner + back_cap + outer.reverse() + front_cap

            for controlpoint in controlpoints:
                p = controlpoint[0].nodes[0]

                if outline.contains(p):
                    plotpart.layers[self.layer_name_laser_dots] += controlpoint
                    
            plotpart.layers[self.layer_name_outline].append(outline.fix_errors())

        # rigidfoils
        for i, rigid in enumerate(self.rib.get_rigidfoils()):
            draw_rigid(rigid, f"{self.rib.name}r{i+1}")

        return plotpart


class SingleSkinRibPlot(RibPlot):
    skin_cut: float | None = None

    def _get_inner_outer(self, x_value: float) -> Tuple[euklid.vector.Vector2D, euklid.vector.Vector2D]:
        # TODO: shift when after the endpoint
        inner, outer = super()._get_inner_outer(x_value)

        if self.skin_cut is None or x_value < self.skin_cut:
            return inner, outer
        else:
            return inner, inner + (inner - outer)

    def _get_singleskin_cut(self, glider: Glider) -> float:
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
        stop = cuts[-1][0]

        contour = euklid.vector.PolyLine2D([])

        if isinstance(self.rib, openglider.glider.rib.SingleSkinRib):
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

        else:

            buerzl = euklid.vector.PolyLine2D([outer_rib.get(stop),
                                 outer_rib.get(stop) + euklid.vector.Vector2D([t_e_allowance, 0]),
                                 outer_rib.get(start) + euklid.vector.Vector2D([t_e_allowance, 0]),
                                 outer_rib.get(start)])

            contour += euklid.vector.PolyLine2D(outer_rib.get(start, stop))
            contour += buerzl
        
        return contour
