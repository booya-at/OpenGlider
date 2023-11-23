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


        print("...")
        print(p)
        print("...")

        p_temp = list(p)

        p_temp[0] = p_temp[0] * profile.curve.nodes[0][0]

        return euklid.vector.Vector2D(p_temp)


    def add_text(self, plotpart: PlotPart) -> None:
        
        posX = self.minirib.front_cut

        p1 = self.get_point(posX, 1)
        p2 = self.get_point(posX, -1)

        p1 = (p1+p2)/2
        p2 = p1 +euklid.vector.Vector2D([0.02,-0.005])

        print(p1)
        print(p2)

        _text = Text(self.minirib.name, p1, p2, size=0.01, align="center", valign=0)


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
        plotpart = PlotPart(material_code=self.minirib.material_code, name=self.minirib.name)

        self.inner = self.minirib.get_flattened(self.cell)
        self.outer = self.inner.offset(self.config.allowance_general, simple=False)

        envelope = self.draw_outline()

        plotpart.layers[self.layer_name_sewing].append(self.inner)
                
        plotpart.layers[self.layer_name_outline].append(envelope)

        self.add_text(plotpart)

        self.plotpart = plotpart

        return plotpart