import vtk
import vtk.qt
vtk.qt.QVTKRWIBase = "QGLWidget"
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from openglider.gui.qt import QtWidgets, QtGui

import openglider.mesh
from openglider.gui.views_3d.actors import MeshView, PanelView
from openglider.gui.views_3d.interactor import Interactor


class View3D(QtWidgets.QWidget):
    show_axes = True
    renderer: vtk.vtkRenderer

    def __init__(self, parent=None):
        super(View3D, self).__init__(parent)
        self.setLayout(QtWidgets.QHBoxLayout(self))

        self.frame = QtWidgets.QFrame()
        self.frame.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.frame)

        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(.2, .3, .4)
        self.renderer.SetViewport(0, 0, 1, 1)

        self.VTKRenderWindow = vtk.vtkRenderWindow()

        self.VTKRenderWindow.AddRenderer(self.renderer)

        self.VTKRenderWindowInteractor = QVTKRenderWindowInteractor(self.frame, rw=self.VTKRenderWindow)
        self.frame.layout().addWidget(self.VTKRenderWindowInteractor)

        self.VTKCamera = vtk.vtkCamera()
        self.VTKCamera.SetClippingRange(0.1, 1000)
        self.VTKCamera.SetFocalPoint(0, 0, -3)
        self.VTKCamera.SetPosition(-15, 0, -3)
        self.VTKCamera.SetRoll(90)
        self.renderer.SetActiveCamera(self.VTKCamera)

        self.VTKRenderWindowInteractor.SetInteractorStyle(Interactor())

        self.VTKRenderWindowInteractor.Initialize()
        #self.VTKRenderWindowInteractor.Start()
        #self.VTKRenderWindowInteractor.ReInitialize()

        self.axes = vtk.vtkAxesActor()
        self.clear()

    def clear(self):
        self.renderer.RemoveAllViewProps()
        if self.show_axes:
            self.show_actor(self.axes)
        self.rerender()

    def show_actor(self, actor):
        self.renderer.AddActor(actor)
        self.VTKRenderWindow.Render()

    def rerender(self):
        self.VTKRenderWindow.Render()


