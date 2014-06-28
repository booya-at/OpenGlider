from openglider.gui.qt import QtGui
import vtk
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class GraphicsWidget(QtGui.QWidget):
    def __init__(self, *graphics):
        super(GraphicsWidget, self).__init__()
        self.gridlayout = QtGui.QGridLayout(self)
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        #print(dir(self))
        self.gridlayout.addWidget(self.vtkWidget)

        self.render_window = self.vtkWidget.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.render_interactor = self.render_window.GetInteractor()
        self.render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        self.renderer.SetBackground(0.1, 0.2, 0.4)
        self.renderer.ResetCamera()

        self.add_graphics(*graphics)

    def add_graphics(self, *graphics):
        for graph in graphics:
            self.renderer.AddActor(graph.actor)

    def show(self):
        self.render_interactor.Initialize()
        self.render_interactor.Start()