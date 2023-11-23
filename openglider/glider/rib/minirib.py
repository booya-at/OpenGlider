from __future__ import annotations

from typing import TYPE_CHECKING
import euklid
import logging
import numpy as np

import pyfoil

import openglider.airfoil
from openglider.glider.rib import Rib

from openglider.airfoil import Profile3D
from openglider.utils.dataclass import dataclass, Field
from openglider.utils.cache import cached_function, cached_property

from openglider.mesh import Mesh, triangulate

if TYPE_CHECKING:
    from openglider.glider.cell import Cell
    from openglider.glider.cell.panel import Panel

logger = logging.getLogger(__name__)

@dataclass
class MiniRib:
    yvalue: float
    front_cut: float
    back_cut: float = 1.0 # | None=None # ?? should be handled by __post_init__ but I dont get it.
    name: str="unnamed_minirib"
    material_code: str="unnamed_material"
   
    

    function: euklid.vector.Interpolation = Field(default_factory=lambda: euklid.vector.Interpolation([]))

    class Config:
        arbitrary_types_allowed = True

    def __post_init__(self) -> None:
        p1_x = 2/3

        if self.function is None or len(self.function.nodes) == 0:
            if self.front_cut > 0:
                if self.back_cut is None:
                    back_cut = 1.
                else:
                    back_cut = self.back_cut
                points = [[self.front_cut, 1], [self.front_cut + (back_cut - self.front_cut) * (1-p1_x), 0]]  #
            else:
                points = [[0, 0]]

            if self.back_cut is not None and self.back_cut < 1.:
                points = points + [[self.front_cut + (self.back_cut-self.front_cut) * p1_x, 0], [self.back_cut, 1]]
            else:
                points = points + [[1., 0.]]

            curve = euklid.spline.BSplineCurve(points).get_sequence(100)
            self.function = euklid.vector.Interpolation(curve.nodes)

    def multiplier(self, x: float) -> float:
        within_back_cut = self.back_cut is None or abs(x) <= self.back_cut
        if self.front_cut <= abs(x) and within_back_cut:
            return min(1, max(0, self.function.get_value(abs(x))))
        else:
            return 1.

    def get_3d(self, cell: Cell) -> Profile3D:
        shape_with_bal = cell.basic_cell.midrib(self.yvalue, True).curve.nodes
        shape_wo_bal = cell.basic_cell.midrib(self.yvalue, False).curve.nodes

        points: list[euklid.vector.Vector3D] = []
        for xval, with_bal, without_bal in zip(
                cell.x_values, shape_with_bal, shape_wo_bal):
            fakt = self.multiplier(xval)  # factor ballooned/unb. (0-1)
            point = without_bal + (with_bal - without_bal) * fakt
            points.append(point)

        return Profile3D(euklid.vector.PolyLine3D(points))

    
    def get_flattened_length_top(self, cell: Cell) -> float:
        line, ik_front_bot, ik_back_bot, ik_front_top, ik_back_top= self._get_flattened_line(cell)

        return line.get(ik_back_top, ik_front_top).get_length()
    
    def get_flattened_length_bot(self, cell: Cell) -> float:
        line, ik_front_bot, ik_back_bot, ik_front_top, ik_back_top= self._get_flattened_line(cell)

        return line.get(ik_front_bot, ik_back_bot).get_length()

    def _get_flattened_line(self, cell: Cell) -> tuple[euklid.vector.PolyLine2D, float, float]:

        # todo cleanup
        flattened_cell = cell.get_flattened_cell()
        left, right = flattened_cell.ballooned
        line = left.mix(right, self.yvalue)

        ik_front_bot = (cell.rib1.profile_2d(self.front_cut) + cell.rib2.profile_2d(self.front_cut))/2
        ik_back_bot = (cell.rib1.profile_2d(self.back_cut) + cell.rib2.profile_2d(self.back_cut))/2

        ik_back_top = (cell.rib1.profile_2d(-self.front_cut) + cell.rib2.profile_2d(-self.front_cut))/2
        ik_front_top = (cell.rib1.profile_2d(-self.back_cut) + cell.rib2.profile_2d(-self.back_cut))/2

        return line, ik_front_bot, ik_back_bot, ik_front_top, ik_back_top

    def draw_panel_marks(self, cell: Cell, panel: Panel) -> euklid.vector.PolyLine2D | None:
        line, ik_front_bot, ik_back_bot, ik_front_top, ik_back_top = self._get_flattened_line(cell)

        ik_interpolation_front, ik_interpolation_back = panel._get_ik_interpolation(cell, numribs=50)

        if panel.is_lower():
            start = max(ik_front_bot, ik_interpolation_front.get_value(self.yvalue))
            stop= min(ik_back_bot, ik_interpolation_back.get_value(self.yvalue))
        else:    
            start = max(ik_front_top, ik_interpolation_front.get_value(self.yvalue))
            stop = min(ik_back_top, ik_interpolation_back.get_value(self.yvalue))

        if start < stop:
            return line.get(start, stop)
        
        #3D shaping cut does not seem to be taken into account

        #return None


    def get_flattened(self, cell: Cell) -> euklid.vector.PolyLine2D:

        profile = self.get_3d(cell).flatten()
        contour = profile.curve


        start_bot = profile.get_ik(self.front_cut*profile.curve.nodes[0][0])
        end_bot = profile.get_ik(profile.curve.nodes[0][0])
        start_top = profile.get_ik(-self.front_cut*profile.curve.nodes[0][0])
        end_top = profile.get_ik(-profile.curve.nodes[0][0])

        nodes_top = euklid.vector.PolyLine2D(contour.get(end_top, start_top))
        nodes_bottom = euklid.vector.PolyLine2D(contour.get(start_bot, end_bot))

        length_minirib = nodes_top.get_length()+ nodes_bottom.get_length()

        length_on_panel = self.get_flattened_length_bot(cell) + self.get_flattened_length_top(cell)
        
        correction_factor = length_on_panel/length_minirib

        logger.info(f"Minirib correction_factor: %s" %correction_factor)

        return_nodes_top = nodes_top * euklid.vector.Vector2D([correction_factor, 1.])
        return_nodes_bottom = nodes_bottom * euklid.vector.Vector2D([correction_factor, 1.])

        return_nodes = euklid.vector.PolyLine2D(return_nodes_top + return_nodes_bottom)

        logger.info(f"Miniribs of Cell: {cell.name} length difference Top and Bot seam: {((length_on_panel-(return_nodes_top.get_length()+return_nodes_bottom.get_length()))*1000)} mm")

        return return_nodes
    
    def get_hull(self, cell: Cell) -> pyfoil.Airfoil:
        """returns the outer contour of the normalized mesh in form
           of a Polyline"""
        
        profile = self.get_3d(cell).flatten()
        contour = profile.curve

        start_bot = profile.get_ik(self.front_cut*profile.curve.nodes[0][0])
        end_bot = profile.get_ik(profile.curve.nodes[0][0])
        start_top = profile.get_ik(-self.front_cut*profile.curve.nodes[0][0])
        end_top = profile.get_ik(-profile.curve.nodes[0][0])

        nodes_top = euklid.vector.PolyLine2D(contour.get(end_top, start_top))
        nodes_bottom = euklid.vector.PolyLine2D(contour.get(start_bot, end_bot))
        
        nodes= euklid.vector.PolyLine2D(nodes_top+nodes_bottom)

        return openglider.airfoil.Profile2D(nodes)
    


    def align_all(self, cell: Cell, data: euklid.vector.PolyLine2D, scale: bool=False) -> euklid.vector.PolyLine3D:
        """align 2d coordinates to the 3d pos of the minirib"""

        rib1 = cell.rib1
        rib2 = cell.rib2 #midrib(self.yvalue, True)

        # ToDo: not correct as ribs are not parallel

        if scale:
            return ((rib1.transformation.apply(data)).mix((rib2.transformation.apply(data)),self.yvalue))
        else:
            return (rib1.rotation_matrix.apply(data).move(rib1.pos)).mix((rib2.rotation_matrix.apply(data).move(rib2.pos)),self.yvalue)
    


    
    


    def get_mesh(self, cell: Cell, filled: bool=True, max_area: float=None) -> Mesh:

        vertices = [(p[0], p[1]) for p in self.get_hull(cell).curve.nodes[:-1]]
        boundary = [list(range(len(vertices))) + [0]]
        hole_centers: list[tuple[float, float]] = []

        if not filled:
            segments = []
            for lst in boundary:
                segments += triangulate.Triangulation.get_segments(lst)
            return Mesh.from_indexed(self.align_all(cell, euklid.vector.PolyLine2D(vertices)).nodes, {'minirib': [(l, {}) for l in segments]}, {})
        else:
            tri = triangulate.Triangulation(vertices, boundary, hole_centers)
            if max_area is not None:
                tri.meshpy_max_area = max_area
            
            tri.name = self.name
            mesh = tri.triangulate()

            points = self.align_all(cell, euklid.vector.PolyLine2D(mesh.points))
            boundaries = {self.name: list(range(len(mesh.points)))}


            minirib_mesh = Mesh.from_indexed(points.nodes, polygons={"miniribs": [(tri, {}) for tri in mesh.elements]} , boundaries=boundaries)
            
            #for hole in self.holes:
            #    if hole_mesh := hole.get_mesh(self):
            #        rib_mesh += hole_mesh

        return minirib_mesh
    

    
