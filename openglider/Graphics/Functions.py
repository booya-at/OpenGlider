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


def tofloat(lst):
    if isinstance(lst, list):
        return map(tofloat, lst)
    else:
        return float(lst)


def ListLinePlot(points):
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
    def __init__(self, pointnumbers, ttype):
        self.pointnumbers = np.array(pointnumbers)
        self.type = ttype
        if _isintlist(self.pointnumbers):
            self.gtype = 'direct'
        else:
            self.gtype = 'indirect'

    #coordinates= list of points (can be nested)
    def addcoordinates(self, coordinates, add="", start=""):
        if isinstance(start, str):
            startval = len(coordinates) - 1
            additionalcoordinates = self.pointnumbers
        else:
            startval = start
            additionalcoordinates = add

        for i in range(len(additionalcoordinates)):
            if depth(additionalcoordinates[i]) > 2:
                self.addcoordinates(coordinates, add=additionalcoordinates[i], start=startval)
            else:
                startval += 1
                if len(coordinates) == 0:
                    coordinates = [additionalcoordinates[i] * 1]
                else:
                    coordinates = np.append(coordinates, [additionalcoordinates[i]], axis=0)
                additionalcoordinates[i, 0] = startval

        if isinstance(start, str):
            self.pointnumbers = additionalcoordinates.transpose()[0,]
            return coordinates
        else:
            return additionalcoordinates


class Point(GraphicObject):
    def __init__(self, pointnumbers):
        super(Point, self).__init__(pointnumbers, 'Point')


class Line(GraphicObject):
    def __init__(self, pointnumbers):
        super(Line, self).__init__(pointnumbers, 'Line')


class Polygon(GraphicObject):
    def __init__(self, pointnumbers):
        super(Polygon, self).__init__(pointnumbers, 'Polygon')

class Graphics(object):
    """Creates a GraphicsObject"""

    def __init__(self, graphicobjects, coordinates=None, rotation=True):
        self.rotation = rotation
        self.coordinates = coordinates
        self.graphicobjects = graphicobjects
        for graphicobject in self.graphicobjects:
            if graphicobject.gtype == 'indirect':
                self.coordinates = graphicobject.addcoordinates(self.coordinates)
        coordinates = np.array(self.coordinates)
        coordinates = [self._2dtest(i) for i in coordinates]
        self.points = vtk.vtkPoints()
        try:
            for coor in coordinates:
                self.points.InsertNextPoint(coor)
        except TypeError:
            pass

        self.lines = vtk.vtkCellArray()
        self.verts = vtk.vtkCellArray()
        self.polygons = vtk.vtkCellArray()

        for graphicobject in self.graphicobjects:
            if graphicobject.type == 'Line':
                self._createline(graphicobject.pointnumbers)
            elif graphicobject.type == 'Point':
                self._createpoint(graphicobject.pointnumbers)
            elif graphicobject.type == 'Polygon':
                self._createpolygon(graphicobject.pointnumbers)

        self.polydata = vtk.vtkPolyData()
        self.polydata.SetPoints(self.points)

        self.polydata.SetLines(self.lines)
        self.polydata.SetVerts(self.verts)
        self.polydata.SetPolys(self.polygons)

        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInput(self.polydata)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self._createwindow()

    def _2dtest(self, arg):
        if len(arg) == 2:
            return [arg[0], arg[1], 0.]
        else:
            return arg

    def _createpoint(self, pointnumbers):
        if depth(pointnumbers) >= 3:
            for p in pointnumbers:
                self._createpoint(p)
        else:
            self.verts.InsertNextCell(len(pointnumbers))
            for p in pointnumbers:
                self.verts.InsertCellPoint(p)

    def _createline(self, pointnumbers):
        if depth(pointnumbers) >= 3:
            for p in pointnumbers:
                self._createline(p)
        else:
            for i in range(len(pointnumbers) - 1):
                line = vtk.vtkLine()
                line.GetPointIds().SetId(0, pointnumbers[i])
                line.GetPointIds().SetId(1, pointnumbers[i + 1])
                self.lines.InsertNextCell(line)
                i += 1

    def _createpolygon(self, pointnumbers):
        if depth(pointnumbers) >= 3:
            for p in pointnumbers:
                self._createpolygon(p)
        else:
            polygon = vtk.vtkPolygon()
            polygon.GetPointIds().SetNumberOfIds(len(pointnumbers))
            i = 0
            for p in pointnumbers:
                polygon.GetPointIds().SetId(i, p)
                i += 1
            self.polygons.InsertNextCell(polygon)

    def _createwindow(self):
        ren1 = vtk.vtkRenderer()
        ren1.AddActor(self.actor)
        ren1.SetBackground(0.1, 0.2, 0.4)
        ren1.ResetCamera()
        renWin = vtk.vtkRenderWindow()
        renWin.AddRenderer(ren1)
        renWin.SetSize(700, 700)
        iren = vtk.vtkRenderWindowInteractor()
        if self.rotation:
            iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
        else:
            iren.SetInteractorStyle(vtk.vtkInteractorStyleRubberBand2D())
        iren.SetRenderWindow(renWin)
        iren.Initialize()
        iren.Start()


class Graphics3D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics3D, self).__init__(graphicsobject, coordinates, rotation=True)


class Graphics2D(Graphics):
    def __init__(self, graphicsobject, coordinates=None):
        super(Graphics2D, self).__init__(graphicsobject, coordinates, rotation=False)
