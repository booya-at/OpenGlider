import collections

from openglider.plots import DrawingArea
from openglider.plots.glider.cell import PanelPlotMaker
from openglider.plots.glider.ribs import RibPlot


class PlotMaker(object):
    PanelPlot = PanelPlotMaker
    RibPlot = RibPlot

    allowance_parallel = 0.012
    allowance_orthogonal = 0.012
    allowance_folded = 0.012
    allowance_general = 0.012
    allowance_diagonals = 0.012
    allowance_trailing_edge = 0.024
    allowance_entry_open = 0.015

    def __init__(self, glider_3d):
        self.glider_3d = glider_3d

        self.panels = collections.OrderedDict()
        self.dribs = collections.OrderedDict()
        self.ribs = []

    def get_panels(self):
        self.panels.clear()
        for cell in self.glider_3d.cells:
            panels = PanelPlotMaker(cell).get_panels(self.glider_3d.attachment_points)
            self.panels[cell] = panels

        return self.panels

    def get_ribs(self):
        self.ribs.clear()
        for rib in self.glider_3d.ribs:
            rib_plot = RibPlot(rib)
            rib_plot.allowance_general = self.allowance_general
            rib_plot.allowance_trailing_edge = self.allowance_trailing_edge
            rib_plot.flatten(self.glider_3d)
            self.ribs.append(rib_plot.plotpart)

    def get_dribs(self):
        self.dribs.clear()
        for cell in self.glider_3d.cells:
            dribs = PanelPlotMaker(cell).get_dribs()
            self.dribs[cell] = dribs

        return self.dribs

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
        return DrawingArea(parts)

    def get_all_parts_grouped(self):
        return self.get_all_parts().group_materials()

