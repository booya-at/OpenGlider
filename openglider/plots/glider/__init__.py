import collections

from openglider.plots.drawing import Layout
from openglider.plots.glider.cell import CellPlotMaker
from openglider.plots.glider.ribs import RibPlot
from openglider.plots.glider.config import PatternConfig


class PlotMaker(object):
    CellPlotMaker = CellPlotMaker
    RibPlot = RibPlot
    DefaultConfig = PatternConfig

    def __init__(self, glider_3d, config=None):
        self.glider_3d = glider_3d
        self.config = self.DefaultConfig(config)

        self.panels = collections.OrderedDict()
        self.dribs = collections.OrderedDict()
        self.ribs = []
        self._cellplotmakers = dict()

    def _get_cellplotmaker(self, cell):
        if cell not in self._cellplotmakers:
            self._cellplotmakers[cell] = self.CellPlotMaker(cell,
                                                            self.glider_3d.attachment_points,
                                                            self.config)

        return self._cellplotmakers[cell]

    def get_panels(self):
        self.panels.clear()
        for cell in self.glider_3d.cells:
            self.panels[cell] = self._get_cellplotmaker(cell).get_panels()

        return self.panels

    def get_ribs(self, rotate=False):
        self.ribs = []
        for rib in self.glider_3d.ribs:
            rib_plot = RibPlot(rib, self.config)

            rib_plot.flatten(self.glider_3d)
            if rotate:
                rib_plot.plotpart.rotate(90, radians=False)
            self.ribs.append(rib_plot.plotpart)

    def get_dribs(self):
        self.dribs.clear()
        for cell in self.glider_3d.cells:
            # missing attachmentpoints []
            dribs = PanelPlotMaker(cell, []).get_dribs(self.glider_3d.attachment_points)
            self.dribs[cell] = dribs

        return self.dribs

    def get_all_grouped(self):
        # create x-raster
        for rib in self.ribs:
            rib.rotate(90, radians=False)

        panels = Layout.stack_row(self.panels.values(), self.config.patterns_align_dist_x)
        ribs = Layout.stack_row(self.ribs, self.config.patterns_align_dist_x)
        dribs = Layout.stack_row(self.dribs.values(), self.config.patterns_align_dist_x)

        panels_grouped = panels.group_materials()
        ribs_grouped = ribs.group_materials()
        dribs_grouped = dribs.group_materials()

        panels_border = panels.draw_border(append=False)
        ribs_border = ribs.draw_border(append=False)
        dribs_border = dribs.draw_border(append=False)

        for material_name, layout in panels_grouped.items():
            layout.parts.append(panels_border.copy())
            layout.add_text("panels_"+material_name)

        for material_name, layout in ribs_grouped.items():
            layout.parts.append(ribs_border.copy())
            layout.add_text("ribs_"+material_name)

        for material_name, layout in dribs_grouped.items():
            layout.parts.append(dribs_border.copy())
            layout.add_text("dribs_"+material_name)

        all_layouts = []
        all_layouts += panels_grouped.values()
        all_layouts += ribs_grouped.values()
        all_layouts += dribs_grouped.values()

        return Layout.stack_column(all_layouts, 0.01, center_x=False)

    def unwrap(self):
        self.get_panels()
        self.get_ribs()
        self.get_dribs()
        return self

    def get_all_parts(self):
        parts = []
        for cell in self.panels.values():
            parts += [p.copy() for p in cell]
        for rib in self.ribs:
            parts.append(rib.copy())
        for dribs in self.dribs.values():
            parts += [p.copy() for p in dribs]
        return DrawingArea(parts)

    def get_all_grouped(self):
        return self.get_all_parts().group_materials()

