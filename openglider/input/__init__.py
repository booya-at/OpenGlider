from __future__ import division
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4 import QtGui, QtCore
from openglider.vector import norm_squared


class MplWidget(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, dynamic=True):
        self.ax_list = []
        self.actual_ax = 0
        self.start_move_pos = self.current_xlim = self.current_ylim = None
        self.start_drag = False
        self.start_move = False
        self.current_pos = (0, 0)
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
            self.fig.canvas.mpl_connect('motion_notify_event', self.drag)
            self.fig.canvas.mpl_connect('button_release_event', self.offclick)
            self.fig.canvas.mpl_connect('scroll_event', self.zoom)

    def updatedata(self):
        for i in self.ax_list:
            i.updatedata()

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
        if event.button == 3:
            self.start_move_pos = (event.x, event.y)
            self.current_xlim = self.ax.get_xlim()
            self.current_ylim = self.ax.get_ylim()
            self.start_move = True
            #self.dragfunc = self._move

        elif event.button == 1:
            for element in self.ax_list:
                if element.point_over(event.xdata, event.ydata):
                    self.actual_ax = element
                    self.start_drag = True
                    #self.dragfunc = self._drag

    # def _drag(self):
    #     pass
    #
    # def _move(self):
    #     pass

    def drag(self, event):
        #if self.dragfunc:
        #    self.dragfunc(event.xdata, event.ydata)
        if self.start_drag:
            # TODO: Check bounds
            x_temp = self.actual_ax.x_list
            y_temp = self.actual_ax.y_list
            pos_temp = self.actual_ax.drag_pos
            x_temp[pos_temp] = event.xdata
            y_temp[pos_temp] = event.ydata
            self.actual_ax.x = x_temp
            self.actual_ax.y = y_temp
            self.actual_ax.updatedata()
            self.fig.canvas.draw()

        elif self.start_move:
            delta_x = (self.start_move_pos[0]-event.x)/self.fig.dpi
            delta_y = (self.start_move_pos[1]-event.y)/self.fig.dpi
            self.ax.set_xlim([self.current_xlim[0]+delta_x, self.current_xlim[1]+delta_x])
            self.ax.set_ylim([self.current_ylim[0]+delta_y, self.current_ylim[1]+delta_y])
            self.fig.canvas.draw()

    def offclick(self, event):
        self.start_drag = False
        self.start_move = False

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

        new_width = (curr_xlim[1]-curr_xlim[0])*factor

        relx = (curr_xlim[1]-event.xdata)/(curr_xlim[1]-curr_xlim[0])
        rely = (curr_ylim[1]-event.ydata)/(curr_ylim[1]-curr_ylim[0])
        self.ax.set_xlim([event.xdata-new_width*(1-relx),
                          event.xdata+new_width*relx])
        self.ax.set_ylim([event.ydata-new_width*(1-rely)/2,
                          event.ydata+new_width*rely/2])
        self.fig.canvas.draw()


class Line():
    def __init__(self, _mpl_widget, x_list, y_list, line_width=1):
        self.mpl = _mpl_widget
        self.mpl.ax_list.append(self)
        #self.points = points
        self.x_list = x_list
        self.y_list = y_list
        self.drag_pos = 0
        self.ax = self.mpl.fig.add_subplot(1, 1, 1)
        self.plot, = self.ax.plot([], [], lw=line_width, color='black', ms=5, marker="o", mfc="r", picker=5)
        self.ax.axis("equal")
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)
        self.updatedata()
        self.ax.relim()
        self.ax.autoscale_view()

    def updatedata(self):
        #self.plot.set_xdata(self.points[:, 0])
        #self.plot.set_ydata(self.points[:, 1])
        self.plot.set_xdata(self.x_list)
        self.plot.set_ydata(self.y_list)

    def point_over(self, x, y, tolerance=1):
        x_bounds = self.ax.get_xlim()
        pixel_scale = (x_bounds[1]-x_bounds[0])/get_ax_size(self.ax, self.mpl.fig)[0]
        for i in range(len(self.x_list)):
            if norm_squared([self.x_list[i]-x, self.y_list[i]-y]) < (tolerance * pixel_scale):
                self.drag_pos = i
                return True
        return False


class BezierCurve:
    def __init__(self):
        pass


def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width = bbox.width * fig.dpi
    height = bbox.height * fig.dpi
    return width, height



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
        mpl2 = MplWidget(QtGui.QWidget(self.mainwidget), width=5, height=4, dpi=100, dynamic=True)

        Line(mpl1, [1, 2, 3, 5, 6], [1, 2, 1, 3, 4], line_width=0)
        Line(mpl2, [2, 3, 4, 2], [2, 3, 1, 0])
        Line(mpl2, [1, 1, 1], [2, 3, 1])
        mpl2.updatedata()

        self.splitter.addWidget(mpl1)
        self.splitter.addWidget(mpl2)

        self.vertikal_layout = QtGui.QVBoxLayout(self.mainwidget)
        self.vertikal_layout.addWidget(self.splitter)
        self.setCentralWidget(self.mainwidget)


if __name__ == "__main__":
    qApp = QtGui.QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()
    sys.exit(qApp.exec_())