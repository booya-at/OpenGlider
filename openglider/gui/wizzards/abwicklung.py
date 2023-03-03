from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Dict, TypeAlias
from openglider.gui.qt import QtWidgets, QtGui
import logging

from openglider.glider.project import GliderProject
from openglider.gui.views_2d import Canvas, LayoutGraphics
from openglider.gui.views.window import GliderWindow
from openglider.plots.glider import PlotMaker
from openglider.vector.drawing import Layout
from openglider.plots import Patterns
from openglider.utils.tasks import Task

if TYPE_CHECKING:
    from openglider.gui.app.app import GliderApp

logger = logging.getLogger(__name__)

class PlotWizzard(GliderWindow):
    copy_project = False

    patterns: Patterns
    plotmaker: PlotMaker
    patterns_class: TypeAlias = Patterns

    def __init__(self, app: GliderApp, project: GliderProject):
        super().__init__(app, project)
        self.logger = logging.getLogger("{}.{}".format(self.__class__.__module__, self.__class__.__name__))

        self.setLayout(QtWidgets.QGridLayout())
        self.directory = None

        self.select_type = QtWidgets.QComboBox()
        self.select_type.addItems([
            "Ribs", "Panels", "Diagonals"
        ])
        self.select_type.currentIndexChanged.connect(self.changed_type)
        self.layout().addWidget(self.select_type, 0, 0)

        self.select_element = QtWidgets.QComboBox()
        self.layout().addWidget(self.select_element, 0, 1)
        self.select_element.currentIndexChanged.connect(self.changed_element)

        self._current_plotpart: LayoutGraphics | None = None
        self.canvas = Canvas()
        self.canvas.locked_aspect_ratio = True
        self.canvas.grid = True
        self.canvas.update_data()
        #self.canvas.addItem(Shape2D(self.project))
        #self.canvas.grid = True
        self.layout().addWidget(self.canvas.get_widget(), 1, 0, 1, 5)
        #self.canvas.update()

        self.label_path = QtWidgets.QLabel()
        self.layout().addWidget(self.label_path, 2, 0, 1, 3)

        self.button_path = QtWidgets.QPushButton("Directory")
        self.button_path.clicked.connect(self.select_path)
        self.layout().addWidget(self.button_path, 2, 3)

        self.button_do = QtWidgets.QPushButton("Unwrap")
        self.button_do.clicked.connect(self.run)
        self.layout().addWidget(self.button_do, 2, 4)

        self.patterns = self.patterns_class(self.project)
        self.plotmaker = self.patterns.plotmaker(self.patterns.project.glider_3d, self.patterns.config)
        self.project = self.patterns.project
        logger.info(f"{self.patterns}, {self.patterns_class}, {self.plotmaker}")

        self.changed_type()

    def changed_type(self) -> None:
        type_str = self.select_type.currentText()
        self.select_element.clear()

        if type_str == "Ribs":
            self.select_element.addItems([f"Rib {i+1}" for i in range(len(self.project.glider_3d.ribs))])
        elif type_str in ("Panels", "Diagonals"):
            self.select_element.addItems([f"Cell {i+1}" for i in range(len(self.project.glider_3d.cells))])

    def changed_element(self) -> None:
        config = self.plotmaker.config
        type_str = self.select_type.currentText()
        element_index = self.select_element.currentIndex()

        dy = self.patterns.config.patterns_align_dist_y
        dx = self.patterns.config.patterns_align_dist_x
        layout = None
        if self._current_plotpart:
            self.canvas.removeItem(self._current_plotpart)

        if type_str == "Ribs":
            rib = self.project.glider_3d.ribs[element_index]
            rib_plot = self.plotmaker.RibPlot(rib)
            rib_plot.flatten(self.project.glider_3d)
            dwg = rib_plot.plotpart
            layout = Layout([dwg])

        elif type_str == "Panels":
            cell = self.project.glider_3d.cells[element_index]
            cell_plot = self.plotmaker.CellPlotMaker(cell, config=config)
            layout_upper = Layout.stack_column(cell_plot.get_panels_upper(), dy)
            layout_lower = Layout.stack_column(cell_plot.get_panels_lower(), dy)
            layout_lower.rotate(180, radians=False)

            layout = Layout.stack_row([layout_upper, layout_lower], dx)

        elif type_str == "Diagonals":
            cell = self.project.glider_3d.cells[element_index]
            cell_plot = self.plotmaker.CellPlotMaker(cell, config=config)
            layout_dribs = Layout.stack_column(cell_plot.get_dribs(), dy)
            layout_straps = Layout.stack_column(cell_plot.get_straps(), dy)

            layout = Layout.stack_row([layout_dribs, layout_straps], 0.2)

        else:
            return
        
        if not layout.is_empty():
            self._current_plotpart = LayoutGraphics(layout)
            #self.canvas.clear()
            self.canvas.addItem(self._current_plotpart)
            self.canvas.update()
        
            
    def select_path(self) -> None:
        home = os.path.expanduser("~")

        if self.project.filename:
            home = os.path.dirname(self.project.filename)
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Abwicklung", home)
        if path:
            self.directory = path
            self.label_path.setText(path)
        self.logger.info(f"directory {path}")

    def run(self) -> None:
        if not self.directory:
            return

        if len(os.listdir(self.directory) ) != 0:
            raise ValueError(f"Direcotry {self.directory} is not empty")

        task = PatternTask(self.patterns, self.directory)
        self.app.task_queue.append(task)

        self.close()


class PatternTask(Task):
    multiprocessed: bool = False
    
    def __init__(self, patterns: Patterns, directory: str):
        self.patterns = patterns
        self.directory = directory

    def __json__(self) -> Dict[str, Any]:
        return {
            "patterns": self.patterns,
            "directory": self.directory
        }

    def get_name(self) -> str:
        return f"Patterns: {self.patterns.project.name} ({self.directory})"
    
    async def run(self) -> None:
        logger.info("patterns running")
        await self.execute(self.patterns.unwrap, self.directory)  # type: ignore
        os.system(f"xdg-open {self.directory}")
    


    