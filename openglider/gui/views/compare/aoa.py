import logging
import math
from openglider.gui.views_2d.dataframe import DataFramePlot
from openglider.gui.widgets.config import ConfigWidget
import pandas
from openglider.gui.qt import QtGui, QtCore, QtWidgets
from openglider.gui.app.app import GliderApp
from openglider.gui.app.state.cache import Cache
from openglider.glider.project import GliderProject
from openglider.utils.dataclass import BaseModel

logger = logging.getLogger(__name__)


class AoAConfig(BaseModel):
    aoa_absolute: bool = False
    aoa_relative: bool = False
    aoa_projection: bool = True


class AoAPlotCache(Cache[GliderProject, pandas.DataFrame]):
    def get_object(self, project_name):
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
        return pandas.DataFrame(
            zip(x_values, aoa_absolute, aoa_relative, aoa_projection),
            columns=["x", "aoa_absolute", "aoa_relative", "aoa_projection"]
            ).set_index("x"), project.color, project.element.name


class AoAView(QtWidgets.QWidget):
    grid = False

    def __init__(self, app: GliderApp):
        super().__init__()
        self.setLayout(QtWidgets.QVBoxLayout())
        self.app = app

        self.plot = DataFramePlot()

        self.config = ConfigWidget(AoAConfig, self)
        self.config.changed.connect(self.update)
        
        self.layout().addWidget(self.config)
        self.layout().addWidget(self.plot)

        self.arc_cache = AoAPlotCache(app.state.projects)

    def update(self):
        logger.info(f"update")
        self.plot.clear()

        changeset = self.arc_cache.get_update()
        config = self.config.config

        for df, color, name in changeset.active:
            self.plot.plotDataFrameColumns(df, config, color, name=name)
            logger.info(f"adding {df.columns}")
