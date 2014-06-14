from openglider.input import ControlPointContainer, ControlPoint, MPL_Bezier, MplWidget
from PyQt4 import QtGui, QtCore
import sys

class MPL_Symmetric_Bezier(MPL_Bezier):
    def __init__(self, controlpoints):
        super(MPL_Symmetric_Bezier, self).__init__(controlpoints)

    @property
    def bezier_curve(self):
        right_pts = [p.point for p in self.controlpoints]
        left_pts = [[-i[0], i[1]] for i in right_pts]
        left_pts.reverse()
        self._bezier_curve.controlpoints = right_pts + left_pts
        return self._bezier_curve

class Shape(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        



class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("application main window")
        self.mainwidget = QtGui.QWidget(self)

        self.splitter = QtGui.QSplitter(self.mainwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        mpl1 = MplWidget(QtGui.QWidget(self.mainwidget), width=10, height=4, dpi=100, dynamic=True)
        points = [[.5, -.2], [.2, -.1], [.0, .0]]
        controlpoints = [ControlPoint(p, locked=[0, 0]) for p in points[0:2]]
        controlpoints += [ControlPoint(points[-1], locked=[1, 0])]
        line1 = MPL_Symmetric_Bezier(controlpoints)  #, mplwidget=mpl1)
        line1.insert_mpl(mpl1)
        mpl1.updatedata()

        self.splitter.addWidget(mpl1)

        self.vertikal_layout = QtGui.QVBoxLayout(self.mainwidget)
        self.vertikal_layout.addWidget(self.splitter)
        self.setCentralWidget(self.mainwidget)


if __name__ == "__main__":
    qApp = QtGui.QApplication(sys.argv)
    aw = ApplicationWindow()
    aw.show()
    sys.exit(qApp.exec_())