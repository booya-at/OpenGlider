from qt import QtCore, QtGui
import widgets


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

if __name__ == '__main__':
    import sys
    from openglider.graphics import Graphics, Polygon, Red
    app = QtGui.QApplication(sys.argv)
    graph = Graphics([Polygon([[0., 0., 0.],
                               [0., 1., 1.],
                               [2., 1., 0.]])], show=False)
    graph2 = Graphics([Red, Polygon([[-1., -2., -3.],
                                     [0., 0., 0.],
                                     [-1., -1., -1.]])], show=False)

    graph_widget = widgets.graphics.GraphicsWidget(graph, graph2)
    graph_widget2 = widgets.graphics.GraphicsWidget(graph, graph2)
    console = widgets.console.ipy_widget()
    window = ApplicationWindow([graph_widget, console, graph_widget2])

    def printdir():
        print(dir(graph_widget.renderer))
        graph.graphicobjects[0].points[0][0] = 2
        graph.redraw()
        graph_widget.renderer.SetBackground(0.1, 0., 0.)
        graph_widget.renderer.ResetCamera()
    console.kernel_manager.kernel.shell.push({'printdir': printdir,
                                              'shell': console.kernel_manager.kernel.shell})
    buttons = widgets.buttons.ButtonWidget({"jo": window.close,
                                            "no": printdir})
    window.add_widgets(buttons)
    window.show()
    graph_widget.show()
    graph_widget2.show()
    sys.exit(app.exec_())