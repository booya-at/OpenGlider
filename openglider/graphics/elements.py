import numpy
import vtk
from functions import _isintlist
from openglider.vector import norm


class GraphicObject(object):
    element_setter = None

    def __init__(self, points, colour=None):
        self._is_direct = _isintlist(points)
        self.points = numpy.array(points)
        self.colour = colour

    #coordinates= list of points (can be nested)
    def add_points(self, graphics):
        """Add Elements Points to the containing class"""
        if self._is_direct:
            return self.points
        else:
            pointnums = [graphics.points.InsertNextPoint(graphics.make_3d(coor)) for coor in self.points]
            return pointnums

    def draw(self, graphics):
        """
        Draw Object into a Graphics-Instance
        """
        cell = graphics.get_cell(self.__class__)
        pointnums = self.add_points(graphics)
        graphics.colours.InsertNextTupleValue(self.colour or graphics.default_colour)
        return cell, pointnums


class Point(GraphicObject):
    element_setter = "SetVerts"

    def __init__(self, pointnumbers, colour=None):
        super(Point, self).__init__(pointnumbers, colour=colour)

    def draw(self, graphics):
        cell, pointnums = super(Point, self).draw(graphics)

        cell.InsertNextCell(len(pointnums))
        for p in pointnums:
            cell.InsertCellPoint(p)
            #graphics.data.SetVerts(cell)


class Line(GraphicObject):
    element_setter = "SetLines"

    def __init__(self, pointnumbers, colour=None):
        super(Line, self).__init__(pointnumbers, colour=colour)

    def draw(self, graphics):
        cell, pointnums = super(Line, self).draw(graphics)
        # colour bugfix for polylines
        for __ in range(len(pointnums) - 2):
            graphics.colours.InsertNextTupleValue(self.colour or graphics.default_colour)

        for i in range(len(pointnums) - 1):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, pointnums[i])
            line.GetPointIds().SetId(1, pointnums[i + 1])
            cell.InsertNextCell(line)

            #graphics.data.SetLines(cell)


class Arrow(GraphicObject):

    def __init__(self, pointnumbers, colour=None):
        super(Arrow, self).__init__(pointnumbers, colour=colour)

    def draw(self, graphics):
        cell, pointnums = super(Arrow, self).draw(graphics)
        assert len(pointnums) == 2

        arrow = vtk.vtkArrowSource()
        p1, p2 = graphics.get_points(*pointnums)
        transform = vtk.vtkTransform()
        transform.Translate(p1)
        length = norm(p2-p1)
        transform.Scale(length, length, length)


class Polygon(GraphicObject):
    element_setter = "SetPolys"

    def __init__(self, pointnumbers, colour=None):
        super(Polygon, self).__init__(pointnumbers, colour=colour)

    def draw(self, graphics):
        cell, pointnums = super(Polygon, self).draw(graphics)

        polygon = vtk.vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds(len(pointnums))
        for i, p in enumerate(pointnums):
            polygon.GetPointIds().SetId(i, p)
        cell.InsertNextCell(polygon)
        #graphics.data.SetPolys(cell)


class Axes(GraphicObject):
    def __init__(self, start=(0., 0., 0.), size=None, label=False):
        super(Axes, self).__init__(start)
        self._is_direct = False
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
            #graphics.renderer.AddActor(axes)


#######################################################################
###################COLOURS#############################################
class RGBColour(object):
    def __init__(self, r=None, g=None, b=None):
        if r is None or g is None or b is None:
            self.colour = [255, 255, 255]
        else:
            self.colour = [r, g, b]

    def draw(self, graphics):
        graphics.default_colour = self.colour

Red = RGBColour(255, 0, 0)
Blue = RGBColour(0, 0, 255)
Green = RGBColour(0, 255, 0)