from __future__ import division
import sys
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.patches
from PyQt4 import QtGui, QtCore
from openglider.vector import norm_squared
from openglider.utils.bezier import BezierCurve


class MplWidget(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, dynamic=True):
        self.cid_id = None
        self.elements = []

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("equal")

        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.setParent(parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.setFocus()
        if dynamic:
           self.fig.canvas.mpl_connect('button_press_event', self.onclick)
           self.fig.canvas.mpl_connect('button_release_event', self.offclick)
           self.fig.canvas.mpl_connect('scroll_event', self.zoom)

    def updatedata(self, i=None):
        if not i is None:
            elements = [self.elements[i]]
        else:
            elements = self.elements
        for element in elements:
            #element.updatedata()
            pass

    @property
    def pixel_scale(self):
        x_bounds = self.ax.get_xlim()
        return (x_bounds[1] - x_bounds[0]) / get_ax_size(self.ax, self.fig)[0]

    def onclick(self, event):
        """
        1: find point (test if the point lies in the drag circle)
            if more than one point is selected take the first
        2: test if point is draggable, only one direction or not draggable
        3: give new position and repaint as long as mouse is pressed

        advanced:
            show which point mouse is over
            if ctrl is pressed:
                snap to grid +  show grid
            if shift is pressed
                snap to other point values
            doublepress:
                enter value for x and y
        """
        if event.xdata is None or event.ydata is None:
            return
        elif event.button == 3:
            startpos = (event.x, event.y)
            self.cid_id = self.fig.canvas.mpl_connect('motion_notify_event', self._move(startpos=startpos))

    def _move(self, startpos):
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()

        def __move(event):
            delta_x = (startpos[0] - event.x) / self.fig.dpi
            delta_y = (startpos[1] - event.y) / self.fig.dpi
            self.ax.set_xlim([current_xlim[0] + delta_x, current_xlim[1] + delta_x])
            self.ax.set_ylim([current_ylim[0] + delta_y, current_ylim[1] + delta_y])
            self.fig.canvas.draw()

        return __move

    def offclick(self, event):
        if not self.cid_id is None:
            self.fig.canvas.mpl_disconnect(self.cid_id)

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

        # new_width = (curr_xlim[1]-curr_xlim[0])*factor

        #relx = (curr_xlim[1]-event.xdata)/(curr_xlim[1]-curr_xlim[0])
        #rely = (curr_ylim[1]-event.ydata)/(curr_ylim[1]-curr_ylim[0])
        #self.ax.set_xlim([event.xdata-new_width*(1-relx),
        #                  event.xdata+new_width*relx])
        #self.ax.set_ylim([event.ydata-new_width*(1-rely)/2,
        #                  event.ydata+new_width*rely/2])
        self.ax.set_xlim(1 / 2 * (curr_xlim[0] * (1 + factor) + curr_xlim[1] * (1 - factor)),
                         1 / 2 * (curr_xlim[1] * (1 + factor) + curr_xlim[0] * (1 - factor)))
        self.ax.set_ylim(1 / 2 * (curr_ylim[0] * (1 + factor) + curr_ylim[1] * (1 - factor)),
                         1 / 2 * (curr_ylim[1] * (1 + factor) + curr_ylim[0] * (1 - factor)))

        self.fig.canvas.draw()


class ControlPointContainer(object):
    def __init__(self, controlpoints, *args):
        self.controlpoints = controlpoints
        self.widgets = None

    def insert_mpl(self, *mplwidgets):
        self.widgets = [[widget, [widget.fig.add_subplot(1, 1, 1)]] for widget in mplwidgets]
        for widget, subplots in self.widgets:
            for point in self.controlpoints:
                subplots[0].add_patch(point.element)
                point.insert(widget.fig, subplots[0])

            subplots[0].axis("equal")
            #subplot.get_xaxis().set_visible(False)
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
        # print("jo")
        self.updatedata()

    def _on_release(self, event):
        for widget, subplot in self.widgets:
            widget.fig.canvas.mpl_disconnect(self.cidmotion)
            widget.fig.canvas.mpl_disconnect(self.cidrelease)


class MPL_Line(ControlPointContainer):
    def __init__(self, controlpoints, line_width=1, mplwidget=None):
        super(MPL_Line, self).__init__(controlpoints)
        # self.controlpoints = controlpoints
        self.linewidth = line_width
        self.line_plot = None

    def insert_mpl(self, *mpl_widgets):
        super(MPL_Line, self).insert_mpl(*mpl_widgets)
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


class MPL_Bezier(ControlPointContainer):
    def __init__(self, controlpoints, line_width=.2, bezier_width=1, mplwidget=None):
        super(MPL_Bezier, self).__init__(controlpoints)
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
        super(MPL_Bezier, self).insert_mpl(*mpl_widgets)
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
        x, y = self.bezier_curve.get_sequence()
        self.bezier_plot.set_xdata(x)
        self.bezier_plot.set_ydata(y)
        for widget, subplots in self.widgets:
            widget.fig.canvas.draw()
            axes = self.line_plot.axes
            axes.draw_artist(self.line_plot)


def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width = bbox.width * fig.dpi
    height = bbox.height * fig.dpi
    return width, height


class ControlPoint:
    lock = None

    def __init__(self, point, locked=(False, False), element=None, visible_move=True):
        self.x_value, self.y_value = point
        self.element = element or matplotlib.patches.Circle(point, 0.03, fc='r', alpha=0.5)
        self.background = None
        self.locked_x, self.locked_y = locked
        self.visible_on_move = visible_move

    @property
    def point(self):
        return self.x_value, self.y_value

    # @point.setter
    # def point(self, point):
    #     if not self.locked_x:
    #         self.x_value = point[0]
    #     if not self.locked_y:
    #         self.y_value = point[1]
    #     self.element.center = self.point

    def update_data(self, x, y):
        if not self.locked_x:
            self.x_value = x
        if not self.locked_y:
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
                self.last_x, self.last_y = self.point
                self.drag_start = event.xdata, event.ydata
                ControlPoint.lock = self
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

    def on_release(self, event):
        'on release we reset the press data'
        if ControlPoint.lock is self:
            ControlPoint.lock = None

            # turn off the rect animation property and reset the background
            self.element.set_animated(False)
            self.background = None

            # redraw the full figure
            self.element.figure.canvas.draw()

    def disconnect(self):
        """
        disconnect all the stored connection ids
        """
        self.element.figure.canvas.mpl_disconnect(self.cidpress)
        self.element.figure.canvas.mpl_disconnect(self.cidrelease)
        self.element.figure.canvas.mpl_disconnect(self.cidmotion)


"""
- by pressing ctrl + space the actual widget -> fullscreen
"""


class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("application main window")
        self.mainwidget = QtGui.QWidget(self)

        self.splitter = QtGui.QSplitter(self.mainwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        mpl1 = MplWidget(QtGui.QWidget(self.mainwidget), width=5, height=4, dpi=100, dynamic=True)
        # mpl2 = MplWidget(QtGui.QWidget(self.mainwidget), width=5, height=4, dpi=100, dynamic=True)
        points = [[.1, .2], [.2, .2], [.3, .6], [.6, .0]]
        controlpoints = [ControlPoint(p, locked=[0, 0]) for p in points]
        controlpoints += [ControlPoint([-p[0], -p[1]], locked=[1, 0]) for p in points]
        #print(mpl1)
        line1 = MPL_Bezier(controlpoints)  #, mplwidget=mpl1)
        line1.insert_mpl(mpl1)
        #line1 = MPL_BezierCurve([1, 2, 3, 5, 6], [1, 2, 1, 3, 4], line_width=1, mplwidget=mpl1, interpolation=False)
        #line2 = MPL_BezierCurve([2, 3, 4, 2], [2, 3, 1, 0], mplwidget=mpl2)
        # line3 = BezierCurve([1, 1, 1], [2, 3, 1], mplwidget=mpl2)
        mpl1.updatedata()
        #mpl2.updatedata()

        self.splitter.addWidget(mpl1)
        #self.splitter.addWidget(mpl2)

        self.vertikal_layout = QtGui.QVBoxLayout(self.mainwidget)
        self.vertikal_layout.addWidget(self.splitter)
        self.setCentralWidget(self.mainwidget)


if __name__ == "__main__":
    qApp = QtGui.QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()
    sys.exit(qApp.exec_())


    # fig = plt.figure()
    #plot = fig.add_subplot(111)
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