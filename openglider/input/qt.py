from PyQt4 import QtCore, QtGui

class ApplicationWindow(QtGui.QMainWindow):
    def __init__(self, widgets=None, title="application main window"):
        super(ApplicationWindow, self).__init__()
        self.setWindowTitle(title)

        self.mainwidget = QtGui.QWidget(self)
        self.splitter = QtGui.QSplitter(self.mainwidget)
        self.splitter.setOrientation(QtCore.Qt.Vertical)

        self.widgets = []
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


class ButtonWidget(QtGui.QSplitter):
    """
    Add a set of Buttons as a widget with functions defined in a dict:
    {"Ok": lambda event: print("Jo!"),
     "Quit": mainwindow.close}
    """
    def __init__(self, buttons):
        super(ButtonWidget, self).__init__()
        self.setOrientation(QtCore.Qt.Horizontal)
        self.buttons = []
        for button, func in buttons.iteritems():
            tha_button = QtGui.QPushButton(button)
            if func:
                tha_button.clicked.connect(func)
            self.buttons.append(tha_button)
            self.addWidget(tha_button)