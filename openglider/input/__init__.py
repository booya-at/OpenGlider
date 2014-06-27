from __future__ import division
import sys
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches
#from pyface.qt import QtGui, QtCore
from PyQt4 import QtGui, QtCore
from openglider.input.qt import ApplicationWindow, ButtonWidget
from openglider.vector import norm_squared
from openglider.utils.bezier import BezierCurve


class ControlPoint:
    lock = None

    def __init__(self, point, locked=(False, False), x_limit=(None, None), y_limit=(None, None),
                 element=None, visible_move=True):
        self.x_value, self.y_value = point
        self.element = element or matplotlib.patches.Circle(point, 0.03, fc='r', alpha=0.5)
        self.background = None
        self.locked_x, self.locked_y = locked
        self.x_limit = x_limit
        self.y_limit = y_limit
        self.visible_on_move = visible_move
        self.last_x = self.last_y = self.drag_start = None
        self.cidrelease = self.cidmotion = self.cidpress = None

    @property
    def point(self):
        return self.x_value, self.y_value

    # @point.setter
    # def point(self, point):
    # if not self.locked_x:
    #         self.x_value = point[0]
    #     if not self.locked_y:
    #         self.y_value = point[1]
    #     self.element.center = self.point

    def update_data(self, x, y):
        if not self.locked_x:
            x = max(x, self.x_limit[0]) if self.x_limit[0] is not None else x
            x = min(x, self.x_limit[1]) if self.x_limit[1] is not None else x
            self.x_value = x
        if not self.locked_y:
            y = max(x, self.y_limit[0]) if self.y_limit[0] is not None else y
            y = min(x, self.y_limit[1]) if self.y_limit[1] is not None else y
            self.y_value = y
        self.element.center = self.point

    def insert(self, figure, subplot):
        """
        Insert control point into figure
        """
        subplot.add_patch(self.element)
        self.cidpress = figure.canvas.mpl_connect('button_press_event', self.on_press)
        self.cidrelease = figure.canvas.mpl_connect('button_release_event', self.on_release)
        self.cidmotion = figure.canvas.mpl_connect('motion_notify_event', self.on_move)

    def on_press(self, event):
        if not event.inaxes != self.element.axes and ControlPoint.lock is None:
            contains, attrd = self.element.contains(event)
            if contains:
                ControlPoint.lock = self

                self.last_x, self.last_y = self.point
                self.drag_start = event.xdata, event.ydata
                self.element.set_animated(True)
                # draw everything but the selected rectangle and store the pixel buffer
                canvas = self.element.figure.canvas
                canvas.draw()
                self.background = canvas.copy_from_bbox(self.element.axes.bbox)
                self.redraw()

    def on_move(self, event):
        if ControlPoint.lock is self and event.inaxes == self.element.axes:
            xpress, ypress = self.drag_start
            dx = event.xdata - xpress
            dy = event.ydata - ypress
            self.update_data(self.last_x + dx, self.last_y + dy)
            if self.visible_on_move:
                self.redraw()

    def on_release(self, event):
        'on release we reset the press data'
        if ControlPoint.lock is self:
            ControlPoint.lock = None
            # turn off the rect animation property and reset the background
            self.element.set_animated(False)
            self.background = None
            # redraw the full figure
            self.element.figure.canvas.draw()

    def redraw(self):
        canvas = self.element.figure.canvas
        axes = self.element.axes
        # restore the background region
        canvas.restore_region(self.background)
        # redraw just the current rectangle
        axes.draw_artist(self.element)
        # blit just the redrawn area
        canvas.blit(axes.bbox)
        self.element.figure.canvas.draw()

    def disconnect(self):
        """
        disconnect all the stored connection ids
        """
        self.element.figure.canvas.mpl_disconnect(self.cidpress)
        self.element.figure.canvas.mpl_disconnect(self.cidrelease)
        self.element.figure.canvas.mpl_disconnect(self.cidmotion)


class ControlPointContainer(object):
    def __init__(self, controlpoints, *args):
        self.controlpoints = controlpoints
        self.widgets = None
        self.cidmotion = self.cidrelease = None

    def insert_mpl(self, *mplwidgets):
        self.widgets = [[widget, [widget.fig.add_subplot(1, 1, 1)]] for widget in mplwidgets]
        for widget, subplots in self.widgets:
            for point in self.controlpoints:
                subplots[0].add_patch(point.element)
                point.insert(widget.fig, subplots[0])

            #subplots[0].axis("equal")
            # subplot.get_xaxis().set_visible(False)
            #subplot.get_yaxis().set_visible(False)

            widget.elements.append(self)
            widget.fig.canvas.mpl_connect('button_press_event', self._on_press)

    def reset_plots(self):
        for widget, subplot in self.widgets:
            subplot.relim()
            subplot.autoscale_view()

    def updatedata(self):
        pass

    def _on_press(self, event):
        for point in self.controlpoints:
            if ControlPoint.lock is point:
                for widget, subplot in self.widgets:
                    self.cidmotion = widget.fig.canvas.mpl_connect('motion_notify_event', self._on_move)
                    self.cidrelease = widget.fig.canvas.mpl_connect('button_release_event', self._on_release)

    def _on_move(self, event):
        self.updatedata()

    def _on_release(self, event):
        """
        Remove event handlers
        """
        for widget, subplot in self.widgets:
            if self.cidmotion is not None:
                widget.fig.canvas.mpl_disconnect(self.cidmotion)
                self.cidmotion = None
            if self.cidrelease is not None:
                widget.fig.canvas.mpl_disconnect(self.cidrelease)
                self.cidrelease = None

    def _resize_controlpoints(self, value=None):
        for cp in self.controlpoints:
            if value:
                cp.element.radius = value


class MplLine(ControlPointContainer):
    def __init__(self, controlpoints, line_width=1, mplwidget=None):
        super(MplLine, self).__init__(controlpoints)
        # self.controlpoints = controlpoints
        self.linewidth = line_width
        self.line_plot = None

    def insert_mpl(self, *mpl_widgets):
        super(MplLine, self).insert_mpl(*mpl_widgets)
        for widget, subplots in self.widgets:
            line_plot = widget.fig.add_subplot(111)
            subplots.append(line_plot)
            self.line_plot, = line_plot.plot([], [], lw=self.linewidth, color='black', ms=5, marker="o", mfc="r",
                                               picker=5)
            self.updatedata()
            for point in self.controlpoints:
                point.visible_on_move = False

    def updatedata(self, event=None):
        self.line_plot.set_xdata([point.x_value for point in self.controlpoints])
        self.line_plot.set_ydata([point.y_value for point in self.controlpoints])
        for widget, subplots in self.widgets:
            widget.fig.canvas.draw()
            axes = self.line_plot.axes
            axes.draw_artist(self.line_plot)


class MplBezier(ControlPointContainer):
    def __init__(self, controlpoints, line_width=.2, bezier_width=1, mplwidget=None):
        super(MplBezier, self).__init__(controlpoints)
        # self.controlpoints = controlpoints
        self.linewidth = line_width
        self.bezier_width = bezier_width
        self._bezier_curve = BezierCurve()
        self.line_plot = self.bezier_plot = None

    @property
    def bezier_curve(self):
        self._bezier_curve.controlpoints = [p.point for p in self.controlpoints]
        return self._bezier_curve

    def insert_mpl(self, *mpl_widgets):
        super(MplBezier, self).insert_mpl(*mpl_widgets)
        for widget, subplots in self.widgets:
            line_plot = widget.fig.add_subplot(111)
            self.line_plot, = line_plot.plot([], [], lw=self.linewidth, color='black', ms=5, marker="o", mfc="r",
                                               picker=5)
            bezier_plot = widget.fig.add_subplot(111)
            self.bezier_plot, = bezier_plot.plot([], [], lw=self.bezier_width, color='black', ms=0, marker="o", mfc="r",
                                                   picker=5)
            subplots += [line_plot, bezier_plot]
            self.updatedata()
            for point in self.controlpoints:
                point.visible_on_move = False

    def updatedata(self, event=None):
        self.line_plot.set_xdata([point.x_value for point in self.controlpoints])
        self.line_plot.set_ydata([point.y_value for point in self.controlpoints])
        x, y = self.bezier_curve.get_sequence(num=50)
        self.bezier_plot.set_xdata(x)
        self.bezier_plot.set_ydata(y)
        for widget, subplots in self.widgets:
            widget.fig.canvas.draw()
            axes = self.line_plot.axes
            axes.draw_artist(self.line_plot)


def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    #width = bbox.span * fig.dpi
    width = bbox.width * fig.dpi
    height = bbox.height * fig.dpi
    return width, height


class MplWidget(FigureCanvas):
    """
    A widget to contain plots and user-input-elements
    """
    def __init__(self, parent=None, width=10, height=8, dpi=200, dynamic=True):
        self.cid_id = None
        self.elements = []

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        #self.fig = Figure()
        super(MplWidget, self).__init__(self.fig)

        self.ax = self.fig.add_subplot(111)
        self.ax.axis("equal")

        super(MplWidget, self).setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        super(MplWidget, self).updateGeometry()
        self.setParent(parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()
        if dynamic:
            self.fig.canvas.mpl_connect('button_press_event', self.on_press)
            self.fig.canvas.mpl_connect('button_release_event', self.on_release)
            self.fig.canvas.mpl_connect('scroll_event', self.zoom)
        self.redraw()

    def updatedata(self, i=None):
        if not i is None:
            elements = [self.elements[i]]
        else:
            elements = self.elements
        for element in elements:
            # element.updatedata()
            pass

    @property
    def pixel_scale(self):
        x_bounds = self.ax.get_xlim()
        return (x_bounds[1] - x_bounds[0]) / get_ax_size(self.ax, self.fig)[0]

    def on_press(self, event):
        """
        move around on right-click
        """
        if event.xdata is None or event.ydata is None:
            return
        elif event.button == 3:
            startpos = (event.x, event.y)
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()

            def move(event_move):
                delta_x = (startpos[0] - event_move.x) / self.fig.dpi
                delta_y = (startpos[1] - event_move.y) / self.fig.dpi
                self.ax.set_xlim([current_xlim[0] + delta_x, current_xlim[1] + delta_x])
                self.ax.set_ylim([current_ylim[0] + delta_y, current_ylim[1] + delta_y])
                self.redraw()

            self.cid_id = self.fig.canvas.mpl_connect('motion_notify_event', move)

    def redraw(self):
        for el in self.elements:
            el._resize_controlpoints(self.pixel_scale * 7)
        self.fig.canvas.draw()

    def on_release(self, event):
        if not self.cid_id is None:
            self.fig.canvas.mpl_disconnect(self.cid_id)
            self.cid_id = None

    def zoom(self, event):
        if event.button == "down":
            factor = 0.05
        else:
            factor = -0.05
        if event.key == 'control':
            factor *= 10
        factor += 1
        curr_xlim = self.ax.get_xlim()
        curr_ylim = self.ax.get_ylim()
        self.ax.set_xlim(1 / 2 * (curr_xlim[0] * (1 + factor) + curr_xlim[1] * (1 - factor)),
                         1 / 2 * (curr_xlim[1] * (1 + factor) + curr_xlim[0] * (1 - factor)))
        self.ax.set_ylim(1 / 2 * (curr_ylim[0] * (1 + factor) + curr_ylim[1] * (1 - factor)),
                         1 / 2 * (curr_ylim[1] * (1 + factor) + curr_ylim[0] * (1 - factor)))
        self.redraw()






if __name__ == "__main__":
    points = [[.1, .2], [.2, .2], [.3, .6], [.6, .0]]
    controlpoints = [ControlPoint(p, locked=[0, 0]) for p in points]
    # print(mpl1)
    line1 = MplBezier(controlpoints)  #, mplwidget=mpl1)
    qApp = QtGui.QApplication(sys.argv)
    widget = MplWidget()
    line1.insert_mpl(widget)
    butons = ButtonWidget({"ok": None})
    aw = ApplicationWindow([butons])
    aw.show()
    sys.exit(qApp.exec_())


    # fig = plt.figure()
    # plot = fig.add_subplot(111)
    #controlpoints = [ControlPoint(p, element=matplotlib.patches.Circle((p[0], p[1]),0.03,fc='r', alpha=0.5)) for p in [[1.2,2.2],[2.2,2.2],[3.3,6.3],[6.3,0.1]]]
    #for point in controlpoints:
    #     point.insert(fig, plot)
    #     plot.add_patch(matplotlib.patches.Circle((point.point[0],point.point[1]), 0.03))
    #     print(point.element, point.point)
    #     p=point
    # ding = matplotlib.patches.Circle((0.2,0.4), 0.03, fc='r', alpha=1)
    # #x,y = controlpoints[0].point
    # #y=float(y)
    # yyyyy=0.3
    # d2 = matplotlib.patches.Circle((0.2,yyyyy),0.03)
    # plot.add_patch(ding)
    # plot.add_patch(d2)
    # print(ding)
    # #plot.redraw()
    # plt.show()
