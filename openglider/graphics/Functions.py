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
from openglider.vector import depth, norm, normalize
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


def draw_glider(glider, num=0, mirror=True, panels=True):
    if mirror:
        temp = glider.copy_complete()
    else:
        temp = glider
    temp.recalc()

    if panels:
        polygons, points = temp.return_polygons(num)
        Graphics([Polygon(polygon) for polygon in polygons], points)
    else:
        ribs = temp.return_ribs(num)
        Graphics([Line(rib) for rib in ribs])
    return True




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
    def __init__(self, points, ttype, colour=None):
        self.type = ttype
        self.__name__ = ttype
        if _isintlist(points):
            self.gtype = 'direct'
        else:
            self.gtype = 'indirect'
        self.points = np.array(points)
        if colour is None:
            self.colour = [255, 255, 255]
        else:
            self.colour = colour

    #coordinates= list of points (can be nested)
    def add_points(self, graphics):
        """Add Elements Points to the containing class"""
        if self.gtype == 'direct':
            return self.points
        else:
            pointnums = [graphics.points.InsertNextPoint(graphics.test_2d(coor)) for coor in self.points]
            return pointnums

    def draw(self, graphics):
        cell = graphics.get_cell(self.type)
        pointnums = self.add_points(graphics)
        #print(self.colour)
        graphics.colours.InsertNextTupleValue(self.colour)
        return cell, pointnums


class Point(GraphicObject):
    def __init__(self, pointnumbers):
        super(Point, self).__init__(pointnumbers, 'Point')

    def draw(self, graphics):
        cell, pointnums = super(Point, self).draw(graphics)

        cell.InsertNextCell(len(pointnums))
        for p in pointnums:
            cell.InsertCellPoint(p)
        graphics.visual_points = cell
        graphics.data.SetVerts(cell)


class Line(GraphicObject):
    def __init__(self, pointnumbers):
        super(Line, self).__init__(pointnumbers, 'Line')

    def draw(self, graphics):
        cell, pointnums = super(Line, self).draw(graphics)
        # colour bug for polylines
        for __ in range(len(pointnums) - 2):
            graphics.colours.InsertNextTupleValue(self.colour)

        for i in range(len(pointnums) - 1):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, pointnums[i])
            line.GetPointIds().SetId(1, pointnums[i + 1])
            cell.InsertNextCell(line)

        graphics.lines = cell
        graphics.data.SetLines(cell)


class Arrow(GraphicObject):
    def __init__(self, pointnumbers):
        super(Arrow, self).__init__(pointnumbers, 'Arrow')

    def draw(self, graphics):
        cell, pointnums = super(Arrow, self).draw(graphics)
        assert len(pointnums) == 2

        arrow = vtk.vtkArrowSource()
        p1, p2 = graphics.get_points(*pointnums)
        transform = vtk.vtkTransform()
        transform.Translate(p1)
        length = norm(p2-p1)
        transform.Scale(length, length, length)
        pass


class Polygon(GraphicObject):
    def __init__(self, pointnumbers):
        super(Polygon, self).__init__(pointnumbers, 'Polygon')

    def draw(self, graphics):
        cell, pointnums = super(Polygon, self).draw(graphics)

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
        self.colours = vtk.vtkUnsignedCharArray()
        self.colours.SetNumberOfComponents(3)
        self.colours.SetName("Colours")

        if not coordinates is None:
            coordinates = np.array(self.coordinates)
            coordinates = [self.test_2d(i) for i in coordinates]
            for coor in coordinates:
                self.points.InsertNextPoint(coor)

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

        self.data.GetCellData().SetScalars(self.colours)

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

    def get_cell(self, name):
        try:
            return getattr(self, 'cell_'+name)
        except AttributeError:
            cellarray = vtk.vtkCellArray()
            setattr(self, 'cell_'+name, cellarray)
            return cellarray

    def get_points(self, *points):
        return [self.points.GetPoint(point_no) for point_no in points]


class Graphics3D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics3D, self).__init__(graphicsobject, coordinates, rotation=True)


class Graphics2D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics2D, self).__init__(graphicsobject, coordinates, rotation=False)