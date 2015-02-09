import sip
try:
    sip.setapi('QDate', 2)
    sip.setapi('QDateTime', 2)
    sip.setapi('QString', 2)
    sip.setapi('QTextStream', 2)
    sip.setapi('QTime', 2)
    sip.setapi('QUrl', 2)
    sip.setapi('QVariant', 2)
except ValueError as e:
    raise RuntimeError('Could not set API version (%s): did you import PyQt4 directly?' % e)
from PyQt4 import QtGui, QtCore


class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self, widgets=None, title="application main window"):
        super(ApplicationWindow, self).__init__()
        self.setWindowTitle(title)
        self.mainwidget = QtGui.QWidget(self)
        self.splitter = QtGui.QSplitter(self.mainwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.widgets = []
        if widgets is not None:
            self.add_widgets(*widgets)
        #for widget in self.widgets:
        #widget.updatedata()
        self.vertikal_layout = QtGui.QVBoxLayout(self.mainwidget)
        self.vertikal_layout.addWidget(self.splitter)
        self.setCentralWidget(self.mainwidget)
    def add_widgets(self, *widgets):
        for widget in widgets:
            self.splitter.addWidget(widget)
        self.widgets.append(widget)