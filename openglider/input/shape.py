from openglider.input import ControlPointContainer, ControlPoint, MplBezier, MplWidget, ApplicationWindow
from PyQt4 import QtGui, QtCore
import sys
from openglider.utils.bezier import fitbezier


class MplSymmetricBezier(MplBezier):
    def __init__(self, controlpoints):
        super(MplSymmetricBezier, self).__init__(controlpoints)

    @property
    def bezier_curve(self):
        right_pts = [p.point for p in self.controlpoints]
        left_pts = [[-p[0], p[1]] for p in right_pts[::-1]]
        self._bezier_curve.controlpoints = left_pts + right_pts
        return self._bezier_curve


def shapeinput(glider):
    front, back = glider.shape
    a = glider.shape_x_values
    control_front = [ControlPoint(p) for p in fitbezier(front)]
    control_back = [ControlPoint(p) for p in fitbezier(back)]
    control_front[0].locked_y = True
    control_front[0].x_limit = (0, None)
    control_back[0].x_limit = (0, None)
    control_back[-1].locked_x = True
    bezier_front = MplSymmetricBezier(control_front)
    bezier_back = MplSymmetricBezier(control_back)

    mpl = MplWidget(dpi=100)
    aww = ApplicationWindow([mpl])
    bezier_front.insert_mpl(mpl)
    bezier_back.insert_mpl(mpl)
    plot_front = mpl.fig.add_subplot(111)
    plot_back = mpl.fig.add_subplot(111)
    pp_front, = plot_front.plot([], [], lw=0.1, color='black', ms=5, marker="o", mfc="g",
                                 picker=5)
    pp_back, = plot_back.plot([], [], lw=0.1, color='black', ms=5, marker="o", mfc="g",
                                picker=5)


    def redraw_plots(event=None):
        pp_front.set_xdata([p[0] for p in front])
        pp_front.set_ydata([p[1] for p in front])
        pp_back.set_xdata([p[0] for p in back])
        pp_back.set_ydata([p[1] for p in back])
        print("jo, updated")


    mpl.fig.canvas.mpl_connect('button_release_event', redraw_plots)
    redraw_plots()


    return aww
    # print(front, back)


if __name__ == "__main__":
    qApp = QtGui.QApplication(sys.argv)
    points = [[.1, .2], [.2, .2], [.3, .6], [.6, .0]]
    #controlpoints = [ControlPoint(p, locked=[0, 0]) for p in points]
    # print(mpl1)
    #line1 = MPL_Symmetric_Bezier(controlpoints)  # , mplwidget=mpl1)
    #aw = ApplicationWindow([line1])
    #aw.show()
    sys.exit(qApp.exec_())