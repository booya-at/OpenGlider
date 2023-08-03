import re
import logging
from typing import Any, List, Tuple
from openglider.mesh.mesh import Mesh

import vtkmodules
import vtkmodules.vtkCommonCore
import vtkmodules.vtkCommonDataModel
import vtkmodules.vtkCommonMath
import vtkmodules.vtkCommonTransforms
import vtkmodules.vtkCommonColor
import vtkmodules.vtkFiltersCore
import vtkmodules.vtkFiltersSources
import vtkmodules.vtkRenderingCore

import euklid
from openglider.lines.lineset import LineSet
from openglider.glider.cell.panel import Panel
from openglider.glider.cell.cell import Cell
import openglider.mesh
from openglider.utils.colors import HeatMap

logger = logging.getLogger(__name__)
colors = vtkmodules.vtkCommonColor.vtkNamedColors()


class Sphere(vtkmodules.vtkRenderingCore.vtkActor):
    color = (1., 1., .3)

    def __init__(self, p: tuple[float, float, float], color: tuple[float, float, float] | None=None):
        super().__init__()
        self.sphere = vtkmodules.vtkFiltersSources.vtkSphereSource()
        self.sphere.SetCenter(p)
        self.sphere.SetRadius(0.1)

        self.mapper = vtkmodules.vtkRenderingCore.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.sphere.GetOutputPort())

        self.SetMapper(self.mapper)

        if color:
            self.color = color
        self.GetProperty().SetColor(*self.color)


class Arrow(vtkmodules.vtkRenderingCore.vtkActor):
    color = (1., 0., 0.)

    def __init__(self, p1: euklid.vector.Vector3D, p2: euklid.vector.Vector3D, shaft: float=0.01, tip: float=.2, color: tuple[float, float, float] | None=None):
        super().__init__()
        if color:
            self.color = color

        self.arrow = vtkmodules.vtkFiltersSources.vtkArrowSource()
        self.arrow.SetShaftRadius(shaft)
        self.arrow.SetTipRadius(4*shaft)
        self.arrow.SetTipLength(tip)
        self.arrow.SetShaftResolution(10)
        self.arrow.SetTipResolution(10)


        start = euklid.vector.Vector3D(p1)
        end = euklid.vector.Vector3D(p2)

        diff = end - start
        length = diff.length()
        v_one = diff.normalized()
        v_two = euklid.vector.Vector3D([v_one[1]+v_one[2], -v_one[0], -v_one[0]]).normalized()
        v_three = v_one.cross(v_two)

        matrix = vtkmodules.vtkCommonMath.vtkMatrix4x4()
        matrix.Identity()
        for i in range(3):
            matrix.SetElement(i, 0, v_one[i])
            matrix.SetElement(i, 1, v_two[i])
            matrix.SetElement(i, 2, v_three[i])

        # Apply the transforms
        self.transform = vtkmodules.vtkCommonTransforms.vtkTransform()
        self.transform.Translate(start)
        self.transform.Concatenate(matrix)
        self.transform.Scale(length, length, length)

        #Create a mapper and actor for the arrow
        self.mapper = vtkmodules.vtkRenderingCore.vtkPolyDataMapper()

        self.mapper.SetInputConnection(self.arrow.GetOutputPort())
        self.SetUserMatrix(self.transform.GetMatrix())
        self.SetMapper(self.mapper)
        self.GetProperty().SetColor(*self.color)


class CellView(vtkmodules.vtkRenderingCore.vtkActor):
    def __init__(self, cell: Cell, midribs: int=2, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.cell = cell
        self.polydata = vtkmodules.vtkCommonDataModel.vtkPolyData()
        self.nodes = vtkmodules.vtkCommonCore.vtkPoints()

        self.lines =  vtkmodules.vtkCommonDataModel.vtkCellArray()
        self.polygons = vtkmodules.vtkCommonDataModel.vtkCellArray()

        self.polydata.SetPoints(self.nodes)
        #self.polydata.SetLines(self.lines)
        self.polydata.SetPolys(self.polygons)

        self.mapper = vtkmodules.vtkRenderingCore.vtkPolyDataMapper()
        self.mapper.SetInputData(self.polydata)

        self.SetMapper(self.mapper)

        self.GetProperty().SetColor(colors.GetColor3d("Tomato"))

        self.draw(midribs)

    def draw(self, midribs: int) -> None:
        midribs += 2
        ribs = [self.cell.midrib(x*1./(midribs-1), arc_argument=False) for x in range(midribs)]
        ribs_ids = []
        #https://www.vtk.org/Wiki/VTK/Examples/Python/GeometricObjects/Display/PolyLine
        # draw lines
        for rib in ribs:
            ribs_ids_this = []
            line = vtkmodules.vtkCommonDataModel.vtkPolyLine()
            line.GetPointIds().SetNumberOfIds(len(rib))
            for i, p in enumerate(rib.curve.nodes):
                p_id = self.nodes.InsertNextPoint(p)
                line.GetPointIds().SetId(i, p_id)
                ribs_ids_this.append(p_id)

            ribs_ids.append(ribs_ids_this)

            self.lines.InsertNextCell(line)

        # draw polys
        for i in range(len(ribs_ids) - 1):
            rib1 = ribs_ids[i]
            rib2 = ribs_ids[i+1]
            for j in range(len(rib1)-1):
                poly = vtkmodules.vtkCommonDataModel.vtkPolygon()
                poly.GetPointIds().SetNumberOfIds(4)
                poly.GetPointIds().SetId(0, rib1[j])
                poly.GetPointIds().SetId(1, rib1[j+1])
                poly.GetPointIds().SetId(2, rib2[j+1])
                poly.GetPointIds().SetId(3, rib2[j])

                self.polygons.InsertNextCell(poly)

            # close trailing edge
            poly = vtkmodules.vtkCommonDataModel.vtkPolygon()
            poly.GetPointIds().SetNumberOfIds(4)
            poly.GetPointIds().SetId(0, rib1[0])
            poly.GetPointIds().SetId(1, rib1[-1])
            poly.GetPointIds().SetId(2, rib2[-1])
            poly.GetPointIds().SetId(3, rib2[0])
            self.polygons.InsertNextCell(poly)


class MeshView(vtkmodules.vtkRenderingCore.vtkActor):
    hex_regex = re.compile(r".*#([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})")
    base_color = (150, 150, 150)
    smooth = True
    colors: vtkmodules.vtkCommonCore.vtkUnsignedCharArray

    def __init__(self) -> None:
        super().__init__()
        self.polydata = vtkmodules.vtkCommonDataModel.vtkPolyData()
        self.nodes = vtkmodules.vtkCommonCore.vtkPoints()
        self.polygons = vtkmodules.vtkCommonDataModel.vtkCellArray()
        self.lines = vtkmodules.vtkCommonDataModel.vtkCellArray()

        self.polydata.SetPoints(self.nodes)
        self.polydata.SetPolys(self.polygons)
        self.polydata.SetLines(self.lines)

        self.mapper = vtkmodules.vtkRenderingCore.vtkPolyDataMapper()
        self.mapper.SetInputData(self.polydata)

        self.colors = vtkmodules.vtkCommonCore.vtkUnsignedCharArray()
        self.colors.SetNumberOfComponents(3)
        self.colors.SetName("Colors")
        self.polydata.GetCellData().SetScalars(self.colors)
        self.GetProperty().SetInterpolationToPhong()
        #self.GetProperty().SetInterpolationToGouraud()

        self.SetMapper(self.mapper)

    def draw_mesh(self, mesh: openglider.mesh.Mesh, colors: bool=True) -> None:
        vertices, polygons, boundaries = mesh.get_indexed()

        for p in vertices:
            self.nodes.InsertNextPoint(list(p))

        line_colors = []
        polygon_colors = []

        for name, polys in polygons.items():

            color_match = self.hex_regex.match(name.upper())
            if color_match:
                color_lst = tuple(int(x, base=16) for x in color_match.groups())
            else:
                color_lst = self.base_color

            for polygon, attributes in polys:
                if len(polygon) == 2:
                    polyline = vtkmodules.vtkCommonDataModel.vtkLine()
                    #polyline.GetPointIds().SetNumberOfIds(2)

                    for i, node_id in enumerate(polygon):
                        polyline.GetPointIds().SetId(i, node_id)

                    self.lines.InsertNextCell(polyline)
                    line_colors.append(color_lst)

                elif len(polygon) > 2:
                    vtk_poly = vtkmodules.vtkCommonDataModel.vtkPolygon()
                    vtk_poly.GetPointIds().SetNumberOfIds(len(polygon))
                    for i, node_id in enumerate(polygon):
                        vtk_poly.GetPointIds().SetId(i, node_id)

                    self.polygons.InsertNextCell(vtk_poly)
                    polygon_colors.append(color_lst)
                else:
                    print("ERRRRR", polygon)
                    continue

        if colors:
            for color_lst in line_colors:
                self.colors.InsertNextTuple(color_lst)
            for color_lst in polygon_colors:
                self.colors.InsertNextTuple(color_lst)

        if self.smooth:
            pdnorm = vtkmodules.vtkFiltersCore.vtkPolyDataNormals()
            pdnorm.SetInputData(self.polydata)
            pdnorm.ComputePointNormalsOn()
            pdnorm.ComputeCellNormalsOn()
            pdnorm.FlipNormalsOff()
            pdnorm.ConsistencyOn()
            pdnorm.Update()
            polydata = pdnorm.GetOutput()

            self.mapper.SetInputData(polydata)



class PanelView(MeshView):
    hex_regex = re.compile(r".*#([0-9A-F]{2})([0-9A-F]{2})([0-9A-F]{2})")

    def __init__(self, panel: Panel, cell: Cell, midribs: int=2) -> None:
        self.cell = cell
        self.panel = panel

        super().__init__()

        self.draw(midribs=midribs)

    def draw(self, midribs: int, left: bool=True, right: bool=True) -> None:
        mesh = openglider.mesh.Mesh()
        panel_mesh = self.panel.get_mesh(self.cell, midribs)

        if left:
            mesh += panel_mesh
        if right:
            mesh += panel_mesh.copy().mirror("y")
            
        self.draw_mesh(mesh)

        color_lst = self.panel.material.get_color_rgb()
        self.GetProperty().SetColor(*color_lst)


class LinesetView(MeshView):
    def __init__(self, lineset: LineSet):
        super().__init__()
        self.lineset = lineset

        self.GetProperty().SetColor(colors.GetColor3d("Grey"))

        self.draw()

    def draw(self, left: bool=True, right: bool=True, line_num: int=4) -> None:
        line_num += 1

        self.lineset.recalc(calculate_sag=True)

        mesh = openglider.mesh.Mesh()
        lineset_mesh = self.lineset.get_mesh(numpoints=line_num)

        if left:
            mesh += lineset_mesh
        if right:
            mesh += lineset_mesh.copy().mirror("y")

        self.draw_mesh(mesh)


class MeshDataView(MeshView):
    def __init__(self, mesh: Mesh, data: list[float]):
        super().__init__()
        self.mesh = mesh
        self.data = data

        self.draw()

    def get_colortable2(self) -> None:
        limit = -4
        data = [max(limit, x) for x in self.data]

        data_min = min(data)
        data_max = max(data)

        colormap = HeatMap(data_min, data_max)

        for value in data:
            color_int = colormap(value)
            self.colors.InsertNextTuple3(*color_int)

    def draw(self) -> None:

        if self.data is not None:
            self.get_colortable2()
            self.draw_mesh(self.mesh, colors=False)
            #self.polydata.GetCellData().SetScalars(self.colors)
        else:
            self.draw_mesh(self.mesh)

        #self.polydata.SetScalarModeToUseCellData()
        #self.polydata.Update()


