from openglider.gui.qt import QtCore, QtGui


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