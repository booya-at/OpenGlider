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


import vtk
import numpy as np
from openglider.Vector import depth
# Quick graphics lib to imitate mathematicas graphics functions


def tofloat(lst):
    if isinstance(lst, list):
        return map(tofloat, lst)
    else:
        return float(lst)


def listlineplot(points):
    if isinstance(points, np.ndarray):
        points = points.tolist()
    if depth(points) == 2:
        Graphics2D([Line(np.transpose(np.array([map(float, range(len(points))), points])))])
    if depth(points) == 3 and len(points[1]) == 2:
        Graphics2D([Line(tofloat(points))])
    if depth(points) == 3 and len(points[1]) == 3:
        Graphics3D([Line(tofloat(points))])


def __isintlist(arg):
    if depth(arg) > 1:
        return max([__isintlist(i) for i in arg])
    else:
        if isinstance(arg, int):
            return 0
        else:
            return 1


def _isintlist(arg):
    if __isintlist(arg) == 0:
        return True
    else:
        return False


class GraphicObject(object):
    def __init__(self, points, ttype):
        self.type = ttype
        if _isintlist(points):
            self.gtype = 'direct'
        else:
            self.gtype = 'indirect'
        self.points = np.array(points)

    #coordinates= list of points (can be nested)
    def add_points(self, graphics):
        """Add Elements Points to the containing class"""
        if self.gtype == 'direct':
            return self.points
        else:
            pointnums = [graphics.points.InsertNextPoint(graphics.test_2d(coor)) for coor in self.points]
            return pointnums


class Point(GraphicObject):
    def __init__(self, pointnumbers):
        super(Point, self).__init__(pointnumbers, 'Point')

    def draw(self, graphics):
        try:
            cell = graphics.visual_points
        except AttributeError:
            cell = vtk.vtkCellArray()
        pointnums = self.add_points(graphics)

        cell.InsertNextCell(len(pointnums))
        for p in pointnums:
            cell.InsertCellPoint(p)
        graphics.visual_points = cell
        graphics.data.SetVerts(cell)


class Line(GraphicObject):
    def __init__(self, pointnumbers):
        super(Line, self).__init__(pointnumbers, 'Line')

    def draw(self, graphics):
        try:
            cell = graphics.lines
        except AttributeError:
            cell = vtk.vtkCellArray()
        pointnums = self.add_points(graphics)

        for i in range(len(pointnums) - 1):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, pointnums[i])
            line.GetPointIds().SetId(1, pointnums[i + 1])
            cell.InsertNextCell(line)

        graphics.lines = cell
        graphics.data.SetLines(cell)


class Polygon(GraphicObject):
    def __init__(self, pointnumbers):
        super(Polygon, self).__init__(pointnumbers, 'Polygon')

    def draw(self, graphics):
        try:
            cell = graphics.polygons
        except AttributeError:
            cell = vtk.vtkCellArray()
        pointnums = self.add_points(graphics)

        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(len(pointnums))
        i = 0
        for p in pointnums:
            polygon.GetPointIds().SetId(i, p)
            i += 1
        cell.InsertNextCell(polygon)
        graphics.polygons = cell
        graphics.data.SetPolys(cell)


class Axes(GraphicObject):
    def __init__(self, start=(0., 0., 0.), size=None, label=False):
        super(Axes, self).__init__(start, 'Axes')
        self.gtype = 'indirect'
        self.size = size
        self.label = label

    def draw(self, graphics):
        transform = vtk.vtkTransform()
        transform.Translate(self.points[0], self.points[1], self.points[2])
        axes = vtk.vtkAxesActor()
        if self.size:
            #transform.Scale(self.size, self.size, self.size)
            axes.SetTotalLength(self.size, self.size, self.size)
        #  The axes are positioned with a user transform
        #axes.SetShaftTypeToCylinder()
        axes.SetUserTransform(transform)
        if not self.label:
            axes.AxisLabelsOff()
        graphics.renderer.AddActor(axes)




class Graphics(object):
    """Creates a GraphicsObject"""

    def __init__(self, graphicobjects, coordinates=None, rotation=True):
        self.rotation = rotation
        self.coordinates = coordinates
        self.graphicobjects = graphicobjects

        self.data = vtk.vtkPolyData()
        self.points = vtk.vtkPoints()

        if not coordinates is None:
            coordinates = np.array(self.coordinates)
            coordinates = [self.test_2d(i) for i in coordinates]
            for coor in coordinates:
                self.points.InsertNextPoint(coor)

        # for graphicobject in self.graphicobjects:
        #     if graphicobject.gtype == 'indirect':
        #         graphicobject.add_points(self)

        self.data.SetPoints(self.points)

        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInput(self.data)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)

        self.renderer = vtk.vtkRenderer()
        self.renderer.AddActor(self.actor)
        self.renderer.SetBackground(0.1, 0.2, 0.4)  # Blue
        self.renderer.ResetCamera()

        for graphicobject in self.graphicobjects:
            graphicobject.draw(self)

        self._createwindow()

    @staticmethod
    def test_2d(arg):
        if len(arg) == 2:
            return [arg[0], arg[1], 0.]
        else:
            return arg

    def _createwindow(self):
        render_window = vtk.vtkRenderWindow()
        render_window.AddRenderer(self.renderer)
        render_window.SetSize(700, 700)
        render_interactor = vtk.vtkRenderWindowInteractor()
        if self.rotation:
            render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        else:
            render_interactor.SetInteractorStyle(vtk.vtkInteractorStyleRubberBand2D())
        render_interactor.SetRenderWindow(render_window)
        render_interactor.Initialize()
        render_interactor.Start()


class Graphics3D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics3D, self).__init__(graphicsobject, coordinates, rotation=True)


class Graphics2D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics2D, self).__init__(graphicsobject, coordinates, rotation=False)