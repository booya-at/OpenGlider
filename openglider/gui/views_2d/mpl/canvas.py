import logging
import math
from typing import Any

from openglider.gui.qt import QtWidgets
from matplotlib.backend_bases import MouseButton

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotCanvas(FigureCanvas):
    """
    Matplotlib Base Widget
    provides a figure, axes and zoom functionality
    """
    zoom_factor = 1.2
    zoom: bool
    grid = False
    dark = False
    preserve_aspect_ratio = True

    def __init__(self, width: int=None, height: int=None, dpi: int=70, zoom: bool=False) -> None:
        self.figure = Figure(dpi=dpi)
        self.axes = self.figure.add_subplot(111)

        self.figure.set_tight_layout(True)
        super().__init__(figure=self.figure)

        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.updateGeometry()

        if zoom is not None:
            self.zoom = zoom

        if self.zoom:
            self._pan_event = None
            self.figure.canvas.mpl_connect("scroll_event", self.zoom_event)

            self.figure.canvas.mpl_connect("button_press_event", self.pan)
            self.figure.canvas.mpl_connect("motion_notify_event", self.pan)
            self.figure.canvas.mpl_connect("button_release_event", self.pan)

        self.update_settings()

    def update_settings(self) -> None:
        #self.axes.clear()

        self.axes.grid(self.grid)

        #if self.preserve_aspect_ratio:
        #    self.axes.set_aspect(1)

        if self.dark:
            self.axes.set_facecolor((.2, .2, .2))
        else:
            self.axes.set_facecolor((1., 1., 1.))

        self.draw()

    def bbox(self) -> tuple[int, int]:
        bbox = self.axes.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        dpi = self.figure.dpi
        #width = bbox.width
        #height = bbox.height
        width, height = bbox.width*dpi, bbox.height*dpi

        return width, height

    def zoom_event(self, event: Any) -> None:
        if event.xdata is None or event.ydata is None:
            return
        # get the current x and y limits
        cur_xlim = self.axes.get_xlim()
        cur_ylim = self.axes.get_ylim()

        scale = {
            "up": 1/self.zoom_factor,
            "down": self.zoom_factor
        }.get(event.button, 1)

        def new_lims(old_lims: tuple[float, float], x: float) -> tuple[float, float]:
            dl = x - min(old_lims)
            dr = max(old_lims) - x

            return x - dl*scale, x + dr*scale

        # set new limits
        self.axes.set_xlim(new_lims(cur_xlim, event.xdata))
        self.axes.set_ylim(new_lims(cur_ylim, event.ydata))

        self.figure.canvas.draw()  # force re-draw

    def pan(self, event: Any) -> None:
        if event.name == 'button_press_event' and event.button == MouseButton.RIGHT:  # begin pan
            self._pan_event = event

        elif event.name == 'button_release_event' and event.button == MouseButton.RIGHT:  # end pan
            self._pan_event = None

        elif event.name == 'motion_notify_event':  # pan
            if self._pan_event is None:
                return

            # Do Pan

            def _pan_update_limits(axis_id: int, pan_event: Any) -> tuple[float, float]:
                """Compute limits with applied pan."""
                assert axis_id in (0, 1)
                if axis_id == 0:
                    lim = self.axes.get_xlim()
                    scale = self.axes.get_xscale()
                else:
                    lim = self.axes.get_ylim()
                    scale = self.axes.get_yscale()

                pixel_to_data = self.axes.transData.inverted()
                data = pixel_to_data.transform_point((pan_event.x, pan_event.y))
                last_data = pixel_to_data.transform_point((self._pan_event.x, self._pan_event.y))

                if scale == 'linear':
                    delta = data[axis_id] - last_data[axis_id]
                    new_lim = lim[0] - delta, lim[1] - delta
                elif scale == 'log':
                    try:
                        delta = math.log10(data[axis_id]) - \
                                math.log10(last_data[axis_id])
                        new_lim = (
                            pow(10., (math.log10(lim[0]) - delta)),
                            pow(10., (math.log10(lim[1]) - delta))
                        )
                    except (ValueError, OverflowError):
                        new_lim = lim  # Keep previous limits
                else:
                    logging.warning('Pan not implemented for scale "%s"' % scale)
                    new_lim = lim
                return new_lim


            self.axes.set_xlim(_pan_update_limits(0, event))
            self.axes.set_ylim(_pan_update_limits(1, event))

            self.figure.canvas.draw()
            self._pan_event = event




