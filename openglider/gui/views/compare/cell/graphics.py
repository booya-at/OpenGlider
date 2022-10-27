from typing import Dict, List
import logging

import pandas
import openglider
import euklid
from openglider.glider.cell.cell import Cell
from openglider.utils.colors import Color
from openglider.glider.project import GliderProject
from openglider.gui.views_2d.canvas import Canvas, LayoutGraphics
from openglider.gui.views.compare.cell.settings import CellPlotLayers
from openglider.gui.app.state.state import GuiProject
from openglider.vector.drawing import Layout, PlotPart


logger = logging.getLogger(__name__)


class CellPlots:
    def __init__(self, cell: Cell) -> None:
        self.cell = cell
    
    def plot(self, config: CellPlotLayers) -> None:
        if config.ballooning:
            self.cell.ballooning


class GliderCellPlots:
    project: GliderProject
    config: CellPlotLayers
    color: Color
    cache: Dict[int, pandas.DataFrame]

    def __init__(self, project: GliderProject, color: Color) -> None:
        self.project = project
        self.color = color
        self.cache = {}
        self.config = CellPlotLayers()
        
    def get(self, cell_no: int, config: CellPlotLayers) -> LayoutGraphics:
        if config != self.config:
            self.cache = {}
            self.config = config.copy()

        if cell_no not in self.cache:

            zero_line = euklid.vector.PolyLine2D([
                [0,0], [1,0]
            ])
            if cell_no < len(self.project.glider_3d.cells):
                cell = self.project.glider_3d.cells[cell_no]
                part = PlotPart([cell.ballooning.draw()], marks=[zero_line])
                dwg = Layout([part])
                dwg.layer_config["cuts"] = {
                    "id": 'outer',
                    "stroke-width": "0.25",
                    "stroke": "red",
                    "stroke-color": f"#{self.color.hex()}",
                    "fill": "none"
                    }
                self.cache[cell_no] = dwg
            
            else:
                self.cache[cell_no] = Layout()
        
        return LayoutGraphics(self.cache[cell_no])

