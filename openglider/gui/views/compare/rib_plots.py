import logging
import math
from openglider.gui.views_2d.dataframe import DataFramePlot
from openglider.gui.widgets.config import ConfigWidget
import pandas
from openglider.gui.qt import QtWidgets
from openglider.gui.app.app import GliderApp
from openglider.gui.state.glider_list import GliderCache
from openglider.utils.dataclass import BaseModel

from openglider.gui.views.compare.base import CompareView

logger = logging.getLogger(__name__)


class RibPlotConfig(BaseModel):
    aoa_absolute: bool = False
    aoa_relative: bool = False
    aoa_projection: bool = True
    chord: bool = False


class RibPlotCache(GliderCache[pandas.DataFrame]):
    def get_object(self, project_name: str) -> pandas.DataFrame:
        project = self.elements[project_name]
        x_values_unscaled = project.element.glider.shape.rib_x_values
        span = max(x_values_unscaled)
        x_values = [x/span for x in x_values_unscaled]
        
        ribs = project.element.glider_3d.ribs[project.element.glider_3d.has_center_cell:]

        att_pt = project.element.glider_3d.get_main_attachment_point().position
        deg = 180/math.pi
        aoa_absolute = [rib.aoa_absolute*deg for rib in ribs]
        aoa_relative = [rib.aoa_relative*deg for rib in ribs]
        aoa_projection = [rib.get_projection(att_pt) for rib in ribs]
        chord = [rib.chord for rib in ribs]
        return pandas.DataFrame(
            zip(x_values, aoa_absolute, aoa_relative, aoa_projection, chord),
            columns=["x", "aoa_absolute", "aoa_relative", "aoa_projection", "chord"]
            ).set_index("x"), project.color, project.element.name


class RibPlotView(CompareView):
    grid = False

    def __init__(self, app: GliderApp):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.app = app

        self.plot = DataFramePlot()

        self.config = ConfigWidget(RibPlotConfig, self)
        self.config.changed.connect(self.update_view)
        
        self.layout().addWidget(self.config)
        self.layout().addWidget(self.plot)

        self.plot_cache = RibPlotCache(app.state.projects)

    def update_view(self) -> None:
        logger.info(f"update")
        self.plot.clear()

        changeset = self.plot_cache.get_update()
        config = self.config.config

        for df, color, name in changeset.active:
            self.plot.plotDataFrameColumns(df, config, color, name=name)
            logger.info(f"adding {df.columns}")
