#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.

# A simple graphics library using vtk and aiming to have a similar syntax as mathematica graphics
import sys
from PyQt4 import QtGui, QtCore
import vtk
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from openglider.graphics.Functions import *
from openglider.input.qt import ApplicationWindow, ButtonWidget

# if __name__ == "__main__":
#     l = Line([[0,0,0.], [1,1,1.]])
#     a = Graphics([l])


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


if __name__ == "__main__":
    qApp = QtGui.QApplication(sys.argv)
    graph = Graphics([Polygon([[0.,0.,0.],[0.,1.,1.],[2.,1.,0.]])], show=False)
    graph2 = Graphics([Red, Polygon([[-1.,-2.,-3.],[0.,0.,0.],[-1.,-1.,-1.]])], show=False)

    widget = GraphicsWidget(graph, graph2)
    widget2 = GraphicsWidget(graph2, graph)
    graph.redraw()
    graph2.redraw()
    buttons = ButtonWidget({"jo": None})
    window = ApplicationWindow([widget, widget2, buttons])
    window.show()
    widget.show()
    widget2.show()
    #widget.render_interactor.Initialize()
    #widget.render_interactor.Start()
    #widget2.render_interactor.Initialize()
    #widget2.render_interactor.Start()
    sys.exit(qApp.exec_())