import collections

from openglider.plots.drawing import DrawingArea
from openglider.plots.glider.cell import PanelPlotMaker
from openglider.plots.glider.ribs import RibPlot
from openglider.plots.glider.config import PatternConfig


class PlotMaker(object):
    PanelPlot = PanelPlotMaker
    RibPlot = RibPlot

    DefaultConfig = PatternConfig

    def __init__(self, glider_3d, config=None):
        self.glider_3d = glider_3d
        self.config = self.DefaultConfig(config)

        self.panels = collections.OrderedDict()
        self.dribs = collections.OrderedDict()
        self.ribs = []

    def get_panels(self):
        self.panels.clear()
        for cell in self.glider_3d.cells:
            panels = self.PanelPlot(cell,
                                    self.glider_3d.attachment_points,
                                    self.config)
            self.panels[cell] = panels.get_panels()

        return self.panels

    def get_ribs(self):
        self.ribs = []
        for rib in self.glider_3d.ribs:
            rib_plot = RibPlot(rib, self.config)
            rib_plot.allowance_general = self.config.allowance_general
            rib_plot.allowance_trailing_edge = self.config.allowance_trailing_edge
            rib_plot.flatten(self.glider_3d)
            self.ribs.append(rib_plot.plotpart)

    def get_dribs(self):
        self.dribs.clear()
        for cell in self.glider_3d.cells:
            # missing attachmentpoints []
            dribs = PanelPlotMaker(cell, []).get_dribs(self.glider_3d.attachment_points)
            self.dribs[cell] = dribs

        return self.dribs

    def get_all_stacked(self, dx=0.01, dy=0.01):
        panels = self.panels
        ribs = self.ribs
        dribs = self.dribs

        plot_panels = DrawingArea.stack_horizontal(panels.values(), dx, dy)
        plot_ribs = DrawingArea.stack_horizontal([[rib] for rib in ribs], dx, dy)
        plot_dribs = DrawingArea.stack_horizontal(dribs.values(), dx, dy)

        return {
            "panels": plot_panels,
            "ribs": plot_ribs,
            "dribs": plot_dribs
        }

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

