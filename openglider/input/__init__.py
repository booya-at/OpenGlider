from __future__ import division
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from PyQt4 import QtGui, QtCore


class mpl_widget(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100, dynamic = True):
        self.ax_list = []
        self.actual_ax = 0
        self.start_drag = False
        self.start_move = False
        self.current_pos = (0,0)
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis("equal")
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self,QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.setParent(parent)
        self.setFocusPolicy( QtCore.Qt.ClickFocus )
        self.setFocus()
        if dynamic:
            self.fig.canvas.mpl_connect('button_press_event', self.onclick)
            self.fig.canvas.mpl_connect('motion_notify_event', self.drag)
            self.fig.canvas.mpl_connect('button_release_event', self.offclick)
            self.fig.canvas.mpl_connect('scroll_event' , self.zoom)

    def updatedata(self):
        for i in self.ax_list:
            i.updatedata()

    def onclick(self, event):
        """
            1: find point (test if the point lies in the drag circle)
                if more then one point is selected take the first
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

        elif event.button == 1:
            for i in self.ax_list:
                if i.point_over(event.xdata, event.ydata):
                    self.actual_ax = i
                    self.start_drag = True

    def drag(self, event):
        if self.start_drag:
            x_temp = self.actual_ax.x
            y_temp = self.actual_ax.y
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
            self.ax.set_xlim([self.current_xlim[0]+delta_x,self.current_xlim[1]+delta_x])
            self.ax.set_ylim([self.current_ylim[0]+delta_y,self.current_ylim[1]+delta_y])
            self.fig.canvas.draw()

    def offclick(self, event):
        self.start_drag = False
        self.start_move = False

    def zoom(self, event):
        if event.button == "down":
            factor = 0.05
        if event.button == 'up':
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
                    event.xdata+new_width*(relx)])
        self.ax.set_ylim([event.ydata-new_width*(1-rely)/2,
                            event.ydata+new_width*(rely)/2])
        self.fig.canvas.draw()





class line():
    def __init__(self, mpl_widget, x, y, l_thick = 1):
        self.mpl = mpl_widget
        self.mpl.ax_list.append(self)
        self.x = x
        self.y = y
        self.drag_pos = 0
        self.ax = self.mpl.fig.add_subplot(111)
        self.plo, = self.ax.plot([],[], lw=l_thick, color='black', ms=5, marker="o", mfc = "r", picker = 5)
        self.ax.axis("equal")
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)
        self.updatedata()
        self.ax.relim()
        self.ax.autoscale_view()

    def updatedata(self):
        self.plo.set_xdata(self.x)
        self.plo.set_ydata(self.y)

    def point_over(self, x, y, tol = 1):
        pixel_scale = pixeldif(self.ax.get_xlim())/get_ax_size(self.ax, self.mpl.fig)
        for i in range(len(self.x)):
            if norm(self.x[i]-x,self.y[i]-y) < ( tol * pixel_scale):
                self.drag_pos = i
                return(True)
        return(False)

def get_ax_size(ax, fig):
    bbox = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    width, height = bbox.width, bbox.height
    width *= fig.dpi
    height *= fig.dpi
    return(width)

def pixeldif(lim):
    return(lim[1]-lim[0])
def norm(x,y):
    return(x**2 + y**2)


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

        mpl1 = mpl_widget(QtGui.QWidget(self.mainwidget), width=5, height=4, dpi=100, dynamic = True)
        mpl2 = mpl_widget(QtGui.QWidget(self.mainwidget), width=5, height=4, dpi=100, dynamic = True)

        line(mpl1,[1,2,3,5,6],[1,2,1,3,4], l_thick=0)
        line(mpl2,[2,3,4,2],[2,3,1,0])
        line(mpl2,[1,1,1],[2,3,1])
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