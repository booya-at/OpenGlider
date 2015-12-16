import collections

from openglider.plots.glider.cell import PanelPlotMaker
from openglider.plots.glider.dribs import get_dribs
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

    def __init__(self, glider):
        self.glider = glider

        self.panels = None

    def get_panels(self):
        self.panels = collections.OrderedDict()
        for cell in self.glider.cells:
            panels = PanelPlotMaker(cell).get_panels(self.glider.attachment_points)
            self.panels[cell] = panels

        return self.panels

    def unwrap(self):
        self.get_panels()
        return self

