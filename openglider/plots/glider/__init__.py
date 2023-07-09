from __future__ import annotations
import collections
import logging
from typing import Any, Dict, List, Optional, TypeAlias
from openglider.glider.cell.cell import Cell
from openglider.glider.glider import Glider
from openglider.utils.config import Config

from openglider.vector.drawing import Layout
from openglider.plots.glider.cell import CellPlotMaker as DefaultCellPlotMaker
from openglider.plots.glider.ribs import RibPlot, SingleSkinRibPlot
from openglider.plots.config import PatternConfig
from openglider.plots.usage_stats import MaterialUsage
from openglider.vector.drawing.part import PlotPart

logger = logging.getLogger(__name__)

PlotPartDict = collections.OrderedDict[Cell, List[PlotPart]]

class PlotMaker:
    glider_3d: Glider
    config: PatternConfig
    
    panels: Layout
    ribs: List[PlotPart]
    dribs: PlotPartDict
    straps: PlotPartDict
    rigidfoils: PlotPartDict

    DefaultConfig: TypeAlias = PatternConfig
    CellPlotMaker: TypeAlias = DefaultCellPlotMaker
    SingleSkinRibPlot = SingleSkinRibPlot
    RibPlot = RibPlot

    def __init__(self, glider_3d: Glider, config: Optional[Config]=None):
        self.glider_3d = glider_3d.copy()
        self.config = self.DefaultConfig(config)
        self.panels = Layout()
        self.ribs = []

        self.dribs = collections.OrderedDict()
        self.straps = collections.OrderedDict()
        self.rigidfoils = collections.OrderedDict()
        self.extra_parts: list[PlotPart] = []
        self._cellplotmakers: Dict[Cell, DefaultCellPlotMaker] = dict()

        self.weight: Dict[str, MaterialUsage] = {}

    def __json__(self) -> Dict[str, Any]:
        return {
            "glider3d": self.glider_3d,
            "config": self.config,
            "panels": self.panels,
            "extra_parts": self.extra_parts,
            #"dribs": self.dribs,
            "ribs": self.ribs
        }

    @classmethod
    def __from_json__(cls, dct: Dict[str, Any]) -> PlotMaker:
        ding = cls(dct["glider3d"], dct["config"])
        ding.panels = dct["panels"]
        ding.ribs = dct["ribs"]
        ding.extra_parts = dct.get("extra_parts", [])
        # ding.dribs = dct["dribs"]

        return ding

    def _get_cellplotmaker(self, cell: Cell) -> CellPlotMaker:
        if cell not in self._cellplotmakers:
            self._cellplotmakers[cell] = self.CellPlotMaker(cell, self.config)

        return self._cellplotmakers[cell]

    def get_panels(self) -> Layout:
        self.panels.clear()
        panels_upper: List[Layout | PlotPart] = []
        panels_lower: List[Layout | PlotPart] = []

        weight = MaterialUsage()

        for cell_no, cell in enumerate(self.glider_3d.cells):
            pm = self._get_cellplotmaker(cell)
            lower = pm.get_panels_lower()
            upper = pm.get_panels_upper()
            panels_lower.append(Layout.stack_column(lower, self.config.patterns_align_dist_y))
            panels_upper.append(Layout.stack_column(upper, self.config.patterns_align_dist_y))

            panel_weight = pm.consumption
            if cell_no > 0 or not self.glider_3d.has_center_cell:
                panel_weight *= 2

            weight += panel_weight


        if self.config.layout_seperate_panels:
            layout_lower = Layout.stack_row(panels_lower, self.config.patterns_align_dist_x)
            layout_lower.rotate(180, radians=False)
            layout_upper = Layout.stack_row(panels_upper, self.config.patterns_align_dist_x)

            self.panels = Layout.stack_row([layout_lower, layout_upper], 2*self.config.patterns_align_dist_x)

        else:
            self.panels = Layout.stack_grid([panels_upper, panels_lower], self.config.patterns_align_dist_x, self.config.patterns_align_dist_y)

        self.weight["panels"] = weight

        return self.panels

    def get_ribs(self, rotate: bool=False) -> None:
        from openglider.glider.rib.singleskin import SingleSkinRib

        weight = MaterialUsage()
        self.ribs = []
        for rib_no, rib in enumerate(self.glider_3d.ribs):
            rib_plot: SingleSkinRibPlot | RibPlot
            if isinstance(rib, SingleSkinRib):
                rib_plot = self.SingleSkinRibPlot(rib, self.config)
            else:
                rib_plot = self.RibPlot(rib, self.config)

            rib_plot.flatten(self.glider_3d)

            for hole in rib.holes:
                self.extra_parts += hole.get_parts(rib)

            rib_weight = rib_plot.weight
            if rib_no == 0:
                if self.glider_3d.has_center_cell:
                    rib_weight = MaterialUsage()
            else:
                rib_weight *= 2
            
            weight += rib_weight

            if rotate:
                rib_plot.plotpart.rotate(-90, radians=False)
            self.ribs.append(rib_plot.plotpart)
        
        self.weight["ribs"] = weight

    def get_dribs(self) -> PlotPartDict:
        self.dribs.clear()
        for cell in self.glider_3d.cells:
            # missing attachmentpoints []
            dribs = self._get_cellplotmaker(cell).get_dribs()
            self.dribs[cell] = dribs[:]

        return self.dribs

    def get_straps(self) -> PlotPartDict:
        self.straps.clear()
        for cell in self.glider_3d.cells:
            # missing attachmentpoints []
            straps = self._get_cellplotmaker(cell).get_straps()
            self.straps[cell] = straps[::-1]

        return self.straps

    def get_rigidfoils(self) -> PlotPartDict:
        # TODO: rib rigids
        self.rigidfoils.clear()

        for cell in self.glider_3d.cells:
            rigidfoils = self._get_cellplotmaker(cell).get_rigidfoils()
            self.rigidfoils[cell] = rigidfoils
        
        return self.rigidfoils

    def get_all_grouped(self) -> Layout:
        # create x-raster
        for rib in self.ribs:
            rib.rotate(-90, radians=False)

        panels = self.panels
        ribs = Layout.stack_row(self.ribs, self.config.patterns_align_dist_x)

        def stack_grid(dct: PlotPartDict) -> Layout:
            layout_lst = [
                Layout.stack_column(p, self.config.patterns_align_dist_y) 
                for p in dct.values()
                ]
            return Layout.stack_row(layout_lst, self.config.patterns_align_dist_x)

        dribs = stack_grid(self.dribs)
        straps = stack_grid(self.straps)
        rigidfoils = stack_grid(self.rigidfoils)

        def group(layout: Layout, prefix: str) -> List[Layout]:
            grouped = layout.group_materials()
            border = layout.draw_border(append=False)

            for material_name, material_layout in grouped.items():
                material_layout.parts.append(border.copy())
                material_layout.add_text(f"{prefix}_{material_name}")
                #material_layout.draw_border(append=True, border=0.1)
            
            return list(grouped.values())

        panels_grouped = group(panels.copy(), "panels")
        ribs_grouped = group(ribs, "ribs")
        dribs_grouped = group(dribs, "dribs")
        straps_grouped = group(straps, "straps")


        panels.add_text("panels_all")

        all_layouts = [panels]
        all_layouts += panels_grouped
        all_layouts += ribs_grouped
        all_layouts += dribs_grouped
        all_layouts += straps_grouped

        if len(rigidfoils.parts):
            rigidfoils.draw_border()
            rigidfoils.add_text(f"rigidfoils")
            all_layouts.append(rigidfoils)

        if len(self.extra_parts):
            extra_parts = Layout.stack_row(self.extra_parts, self.config.patterns_align_dist_x)
            all_layouts += group(extra_parts, "extra_parts")

        return Layout.stack_column(all_layouts, 0.1, center_x=False)

    def unwrap(self) -> PlotMaker:
        self.get_panels()
        self.get_ribs()
        self.get_dribs()
        self.get_straps()
        self.get_rigidfoils()
        return self
