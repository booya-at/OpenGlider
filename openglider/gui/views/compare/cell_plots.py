import logging
from openglider.gui.views_2d.dataframe import DataFramePlot
from openglider.gui.widgets.config import ConfigWidget
import pandas
from openglider.gui.qt import QtWidgets
from openglider.gui.app.app import GliderApp
from openglider.gui.state.glider_list import GliderCache
from openglider.utils.dataclass import BaseModel

from openglider.gui.views.compare.base import CompareView

logger = logging.getLogger(__name__)


class CellPlotConfig(BaseModel):
    width: bool = False
    aspect_ratio: bool = True
    area: bool = False
    projected_area: bool = False


class CellPlotCache(GliderCache[pandas.DataFrame]):
    def get_object(self, project_name: str) -> pandas.DataFrame:
        project = self.elements[project_name]
        x_values_unscaled = project.element.glider.shape.cell_x_values
        span = max(x_values_unscaled)
        x_values = [x/span for x in x_values_unscaled]
        
        data = [
            (x, cell.span, cell.aspect_ratio, cell.area, cell.projected_area)
            for x, cell in zip(x_values, project.element.glider_3d.cells)
        ]

        return pandas.DataFrame(
            data,
            columns=["x", "width", "aspect_ratio", "area", "projected_area"]
            ).set_index("x"), project.color, project.element.name


class CellPlotView(QtWidgets.QWidget, CompareView):
    grid = False

    def __init__(self, app: GliderApp):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.app = app

        self.plot = DataFramePlot()

        self.config = ConfigWidget(CellPlotConfig, self)
        self.config.changed.connect(self.update_view)
        
        self.layout().addWidget(self.config)
        self.layout().addWidget(self.plot)

        self.plot_cache = CellPlotCache(app.state.projects)

    def update_view(self) -> None:
        logger.info(f"update")
        self.plot.clear()

        changeset = self.plot_cache.get_update()
        config = self.config.config

        for df, color, name in changeset.active:
            self.plot.plotDataFrameColumns(df, config, color, name=name)
            logger.info(f"adding {df.columns}")
