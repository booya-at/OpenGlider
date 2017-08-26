# ! /usr/bin/python2
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

import vtk

from openglider.graphics.functions import depth, tofloat
from openglider.graphics.elements import *
# from openglider.graphics.qt import ApplicationWindow

    # problems with this line on ubuntu 15.04


class Graphics(object):
    """Creates a Graphics Instance"""

    def __init__(self, graphicobjects, coordinates=None, rotation=True, show=True):
        self.allow_rotation = rotation
        self.coordinates = coordinates
        self.graphicobjects = graphicobjects
        self.vtk_cells = {}

        self.data = vtk.vtkPolyData()
        self.points = vtk.vtkPoints()
        self.colours = vtk.vtkUnsignedCharArray()
        self.default_colour = [255, 255, 255]  # white
        self.colours.SetNumberOfComponents(3)
        self.colours.SetName("Colours")
        self.actor = vtk.vtkActor()

        self.redraw()

        if show:
            self.show()

    @staticmethod
    def make_3d(arg):
        if len(arg) == 2:
            return [arg[0], arg[1], 0.]
        elif len(arg) == 3:
            return list(arg)
        else:
            raise ValueError("Only 2D- or 3D-Vectors allowed")

    def redraw(self):
        self.data.Reset()
        self.points.Reset()
        self.colours.Reset()

        if not self.coordinates is None:
            for coor in self.coordinates:
                self.points.InsertNextPoint(self.make_3d(coor))

        #BUGFIX, this disables colours partly for polylines, colour has to be set in Line(points, colour=...)
        #for graphicobject in self.graphicobjects:
        #    graphicobject.draw(self)
        for graphicobject in self.graphicobjects:
            if hasattr(graphicobject, 'element_setter') and graphicobject.element_setter == 'SetLines':
                graphicobject.draw(self)
        for graphicobject in self.graphicobjects:
            if not hasattr(graphicobject, 'element_setter') or not graphicobject.element_setter == 'SetLines':
                graphicobject.draw(self)

        self.data.SetPoints(self.points)

        # Set element types (zb: self.data.SetPolys(poly_cell)
        for el_cls, el_cell_array in self.vtk_cells.iteritems():
            if el_cls.element_setter is not None:
                getattr(self.data, el_cls.element_setter)(el_cell_array)

        self.data.GetCellData().SetScalars(self.colours)

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.data)
        self.actor.SetMapper(mapper)

    def show(self):
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.2, 0.4)  # Blue
        self.renderer.ResetCamera()
        self.renderer.AddActor(self.actor)
        render_window = vtk.vtkRenderWindow()
        render_window.SetSize(700, 700)
        render_window.AddRenderer(self.renderer)
        render_interactor = vtk.vtkRenderWindowInteractor()
        if self.allow_rotation:
            render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        else:
            render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleRubberBand2D())
        render_interactor.SetRenderWindow(render_window)
        render_interactor.Initialize()
        render_interactor.Start()

    def get_cell(self, graphics_cls):
        """
        Get a vtkCellArray container
        """
        if graphics_cls not in self.vtk_cells:
            self.vtk_cells[graphics_cls] = vtk.vtkCellArray()
        return self.vtk_cells[graphics_cls]

    def get_points(self, *points):
        return [self.points.GetPoint(point_no) for point_no in points]


class Graphics3D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics3D, self).__init__(graphicsobject, coordinates, rotation=True)


class Graphics2D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics2D, self).__init__(graphicsobject, coordinates, rotation=False)


def show(*graphics):
    allow_rotation = True

    render_window = vtk.vtkRenderWindow()
    render_window.SetSize(700, 700)
    render_interactor = vtk.vtkRenderWindowInteractor()
    if allow_rotation:
        render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
    else:
        render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleRubberBand2D())

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.1, 0.2, 0.4)  # Blue
    renderer.ResetCamera()
    for g in graphics:
        g.redraw()
        renderer.AddActor(g.actor)

    render_interactor.SetRenderWindow(render_window)
    render_window.AddRenderer(renderer)
    render_interactor.Initialize()
    render_interactor.Start()


def listlineplot(points):
    if isinstance(points, numpy.ndarray):
        points = points.tolist()
    if depth(points) == 2:
        Graphics2D([Line(numpy.transpose(numpy.array([map(float, range(len(points))), points])))])
    if depth(points) == 3 and len(points[1]) == 2:
        Graphics2D([Line(tofloat(points))])
    if depth(points) == 3 and len(points[1]) == 3:
        Graphics3D([Line(tofloat(points))])


def draw_glider(glider, num=0, mirror=True, panels=True):
    if mirror:
        temp = glider.copy_complete()
    else:
        temp = glider

    ribs = temp.return_ribs(num)

    if panels:
        points = numpy.concatenate(ribs)
        polygons = temp.return_polygon_indices(ribs)
        Graphics([Polygon(polygon) for polygon in polygons], points)
    else:
        Graphics([Line(rib) for rib in ribs])
    return True
