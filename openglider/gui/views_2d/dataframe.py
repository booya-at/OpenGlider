import re
from typing import List, Any, Optional
from openglider.gui.qt import QtCore, QtGui, QtWidgets
from openglider.utils.colors import Color, colorwheel
import pyqtgraph
import logging
import pandas
import numpy
from openglider.vector.drawing import Layout

logger = logging.getLogger(__name__)

class DataFramePlot(pyqtgraph.PlotWidget):
    log_x = False
    log_y = False
    grid = False

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.column_plots = {}
        self.addLegend()
    
    def plotDataFrameColumns(self, dataframe: pandas.DataFrame, config: Any, color: Color, name: Optional[str]=None) -> None:
        x = dataframe.index.tolist()
        for attr in config.__annotations__:
            if getattr(config, attr):
                y = dataframe[attr].dropna().tolist()

                pen = pyqtgraph.mkPen(color=f"#{color.hex()}")
                self.plot(x, y, name=name, pen=pen)


    def plotDataFrame(self, dataframe: pandas.DataFrame, columns: List[str]=None, force_new: bool=False) -> None:
        if columns is None:
            _columns: pandas.Index = dataframe.columns
            columns = _columns.tolist()
        
        colors = colorwheel(len(columns))
        for i, column in enumerate(columns):
            data = dataframe[column].dropna()
            x = data.index.tolist()
            y = data.tolist()
            if column in self.column_plots and not force_new:
                self.column_plots[column].setData(x, y)
            else:
                pen = pyqtgraph.mkPen(color=colors[i])
                plot = self.plot(x, y, name=column, pen=pen)
                #plot.getViewBox().invertY(True)
                self.column_plots[column] = plot
