from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, Any

import euklid
from openglider.vector.drawing import PlotPart
import openglider.mesh as mesh
import openglider.mesh.triangulate
from openglider.utils.dataclass import BaseModel
from openglider.vector.mapping import Mapping, Mapping3D
from openglider.vector.projection import flatten_list
from openglider.vector.unit import Length, Percentage

if TYPE_CHECKING:
    from openglider.glider.cell import Cell
    from openglider.glider.rib import Rib

logger = logging.getLogger(__name__)


class DiagonalSide(BaseModel):
    """
    Connection between a diagonal and a rib
    """
    center: Percentage
    width: Percentage | Length
    
    height: float


    @property
    def is_lower(self) -> bool:
        return self.height == -1
    
    @property
    def is_upper(self) -> bool:
        return self.height == 1
    
    def _get_position(self, distance: Length, rib: Rib) -> Percentage:
        ik = rib.profile_2d.get_ik(self.center)
        ik_2 = rib.profile_2d.curve.walk(ik, distance.si/rib.chord)
        p = rib.profile_2d.curve.get(ik_2)

        if ik_2 > rib.profile_2d.noseindex:
            return Percentage(p[0])
        else:
            return -Percentage(p[0])
        
    def start_x(self, rib: Rib) -> Percentage:
        if isinstance(self.width, Length):
            return self._get_position(-self.width/2, rib)
        else:
            return self.center - self.width/2
    
    def end_x(self, rib: Rib) -> Percentage:
        if isinstance(self.width, Length):
            return self._get_position(self.width/2, rib)
        else:
            return self.center + self.width/2

    def get_curve(self, rib: Rib) -> euklid.vector.PolyLine3D:
            # Is it at 0 or 1?
            if self.is_lower or self.is_upper:
                factor = 1
                if self.is_upper:
                    factor = -1
                
                profile = rib.get_hull()

                front_ik = profile.get_ik(self.start_x(rib) * factor)
                back_ik = profile.get_ik(self.end_x(rib) * factor)

                return rib.profile_3d.curve.get(front_ik, back_ik)
                #return euklid.vector.PolyLine3D(rib.profile_3d[front:back].data.tolist())
            else:
                return euklid.vector.PolyLine3D([
                    rib.align(rib.profile_2d.align([self.start_x, self.height])),
                    rib.align(rib.profile_2d.align([self.end_x, self.height]))
                ])


class DiagonalRib(BaseModel):
    left: DiagonalSide
    right: DiagonalSide

    material_code: str=""
    name: str="unnamed"

    num_folds: int=1

    hole_num: int=0
    hole_border_side :float=0.2
    hole_border_front_back: float=0.15

    def copy(self, **kwargs: Any) -> DiagonalRib:
        return copy.copy(self)

    @property
    def is_upper(self) -> bool:
        return self.left.is_upper and self.right.is_upper
    
    @property
    def is_lower(self) -> bool:
        return self.left.is_lower and self.right.is_lower

    def mirror(self) -> None:
        self.left ,self.right = self.right, self.left

    def get_center_length(self, cell: Cell) -> float:
        p1 = cell.rib1.point(self.left.center)
        p2 = cell.rib2.point(self.right.center)
        return (p2 - p1).length()

    def get_3d(self, cell: Cell) -> tuple[euklid.vector.PolyLine3D, euklid.vector.PolyLine3D]:
        """
        Get 3d-Points of a diagonal rib
        :return: (left_list, right_list)
        """
        left = self.left.get_curve(cell.rib1)
        right = self.right.get_curve(cell.rib2)

        return left, right

    def get_mesh(self, cell: Cell, insert_points: int=10, project_3d: bool=False, hole_res: int = 40) -> mesh.Mesh:
        """
        get a mesh from a diagonal (2 poly lines)
        """
        left, right = self.get_3d(cell)
        left_2d, right_2d = self.get_flattened(cell)
        
        envelope_2d = left_2d.nodes
        envelope_3d = left.nodes


        def get_list_3d(p1: euklid.vector.Vector3D, p2: euklid.vector.Vector3D) -> list[euklid.vector.Vector3D]:
            return [
                p1 + (p2-p1) * ((i+1)/(insert_points+1))
                for i in range(insert_points)
            ]
        def get_list_2d(p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> list[euklid.vector.Vector2D]:
            return [
                p1 + (p2-p1) * ((i+1)/(insert_points+1))
                for i in range(insert_points)
            ]

        envelope_2d += get_list_2d(left_2d.nodes[-1], right_2d.nodes[-1])
        envelope_3d += get_list_3d(left.nodes[-1], right.nodes[-1])

        envelope_2d += right_2d.reverse().nodes
        envelope_3d += right.reverse().nodes

        envelope_2d += get_list_2d(right_2d.nodes[0], left_2d.nodes[0])
        envelope_3d += get_list_3d(right.nodes[0], left.nodes[0])
        
        boundary_nodes = list(range(len(envelope_2d)))
        boundary = [boundary_nodes+[0]]
        
        holes, hole_centers = self.get_holes(cell, hole_res)

        triangulation_points = envelope_2d[:]
        
        for curve in holes:
            start_index = len(triangulation_points)
            hole_vertices = curve.tolist()[:-1]
            hole_indices = list(range(len(hole_vertices))) + [0]
            triangulation_points += hole_vertices
            boundary.append([start_index + i for i in hole_indices])

        hole_centers_lst = [(p[0], p[1]) for p in hole_centers]
        tri = openglider.mesh.triangulate.Triangulation([(p[0], p[1]) for p in triangulation_points], boundary, hole_centers_lst)
        tri_mesh = tri.triangulate()

        # map 2d-points to 3d-points

        # todo: node_no = kgv(len(left), len(right))
        node_no = 100

        mapping_2d = Mapping([right_2d.resample(node_no), left_2d.resample(node_no)])
        mapping_3d = Mapping3D([right.resample(node_no), left.resample(node_no)])

        points_3d: list[euklid.vector.Vector3D] = []

        for point_3d, point_2d in zip(envelope_3d, tri_mesh.points[:len(envelope_2d)]):
            vector_3d = euklid.vector.Vector3D(point_3d)
            points_3d.append(vector_3d)

        for point in tri_mesh.points[len(envelope_2d):]:
            ik = mapping_2d.get_iks(point)
            points_3d.append(mapping_3d.get_point(*ik))

        drib_mesh = mesh.Mesh.from_indexed(points_3d, {"diagonals": [(p, {}) for p in tri_mesh.elements]}, boundaries={"diagonals": boundary_nodes})

        min_size = drib_mesh.polygon_size()[0]
        if  min_size < 1e-20:
            raise Exception(f"min polygon size: {min_size} in drib: {self.name}")

        return drib_mesh


    def get_holes(self, cell: Cell, points: int=40) -> tuple[list[euklid.vector.PolyLine2D], list[euklid.vector.Vector2D]]:
        left, right = self.get_flattened(cell)

        len_left = left.get_length()
        len_right = right.get_length()

        def get_point(x: float, y: float) -> euklid.vector.Vector2D:
            p1 = left.get(left.walk(0, len_left*x))
            p2 = right.get(right.walk(0, len_right*x))

            return p1 + (p2-p1)*y
        
        holes = []
        centers = []
        
        if self.hole_num == 2:
            holes = [
                euklid.spline.BSplineCurve([
                    get_point(self.hole_border_side, 0.5),
                    get_point(self.hole_border_side, self.hole_border_front_back),
                    get_point(0.5-self.hole_border_side/2, self.hole_border_front_back),
                    get_point(0.5-self.hole_border_side/2, 1-self.hole_border_front_back),
                    get_point(self.hole_border_side, 1-self.hole_border_front_back),
                    get_point(self.hole_border_side, 0.5),
                ]).get_sequence(points),

                euklid.spline.BSplineCurve([
                    get_point(0.5+self.hole_border_side/2, 0.5),
                    get_point(0.5+self.hole_border_side/2, self.hole_border_front_back),
                    get_point(1-self.hole_border_side, self.hole_border_front_back),
                    get_point(1-self.hole_border_side, 1-self.hole_border_front_back),
                    get_point(0.5+self.hole_border_side/2, 1-self.hole_border_front_back),
                    get_point(0.5+self.hole_border_side/2, 0.5),
                ]).get_sequence(points),

            ]

            centers = [
                get_point(0.25 + self.hole_border_side/4, 0.5),
                get_point(0.75 - self.hole_border_side/4, 0.5),
            ]

        return holes, centers

    def get_flattened(self, cell: Cell, ribs_flattened: Any=None) -> tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]:
        first, second = self.get_3d(cell)
        left, right = flatten_list(first, second)
        return left, right

    def get_average_x(self) -> Percentage:
        """
        return average x value for sorting
        """
        return (self.left.center + self.right.center)/2


class TensionStrap(DiagonalRib):
    hole_num: int=0

    def __init__(self, left: Percentage, right: Percentage, width: Percentage | Length, height: float=-1, **kwargs: Any) -> None:
        """
        Similar to a Diagonalrib but always connected to the bottom-sail.
        :param left: left center of TensionStrap as x-value
        :param right: right center of TesnionStrap as x-value
        :param width: width of TensionStrap
        :param material_code: color/material-name (optional)
        :param name: name of TensionStrap (optional)
        """
        
        left_side = DiagonalSide(center=left, width=width, height=height)
        right_side = DiagonalSide(center=right, width=width, height=height)

        super().__init__(left=left_side, right=right_side, **kwargs)
    
    def __json__(self) -> dict[str, Any]:
        return {
            "left": self.left.center,
            "right": self.right.center,
            "width": (self.left.width + self.right.width)/2,
            "height": self.left.height
        }

class TensionLine(TensionStrap):
    def __init__(self, left: Percentage, right: Percentage, material_code: str="", name: str=""):
        """
        Similar to a TensionStrap but with fixed width (0.01)
        :param left: left center of TensionStrap as x-value
        :param right: right center of TesnionStrap as x-value
        :param material_code: color/material-name
        :param name: optional argument names
        """
        super().__init__(left, right, Length(0.01), material_code=material_code, name=name)

    def __json__(self) -> dict[str, Any]:
        return {"left": self.left,
                "right": self.right,
                "material_code": self.material_code,
                "name": self.name
            }

    def get_length(self, cell: Cell) -> float:
        rib1 = cell.rib1
        rib2 = cell.rib2
        left = rib1.profile_3d[rib1.profile_2d(self.left)]
        right = rib2.profile_3d[rib2.profile_2d(self.right)]

        return (left - right).length()

    def get_center_length(self, cell: Cell) -> float:
        return self.get_length(cell)

    def mirror(self) -> None:
        self.left, self.right = self.right, self.left

    def get_mesh(self, cell: Cell, insert_points: int=10, project_3d: bool=False) -> mesh.Mesh:
        boundaries = {}
        rib1 = cell.rib1
        rib2 = cell.rib2
        p1 = rib1.profile_3d[rib1.profile_2d(self.left)]
        p2 = rib2.profile_3d[rib2.profile_2d(self.right)]
        boundaries[rib1.name] = [0]
        boundaries[rib2.name] = [1]
        return mesh.Mesh.from_indexed([p1, p2], {"tension_lines": [((0, 1), {})]}, boundaries=boundaries)


class FingerDiagonal(BaseModel):
    left: DiagonalSide
    right: DiagonalSide

    material_code: str=""
    name: str="unnamed"

    curve_factor: float

    def mirror(self) -> None:
        self.left ,self.right = self.right, self.left

    def get_center_length(self, cell: Cell) -> float:
        p1 = cell.rib1.point(self.left.center)
        p2 = cell.rib2.point(self.right.center)
        return (p2 - p1).length()

    def get_3d(self, cell: Cell) -> tuple[euklid.vector.PolyLine3D, euklid.vector.PolyLine3D]:
        """
        Get 3d-Points of a diagonal rib
        :return: (left_list, right_list)
        """
        left = self.left.get_curve(cell.rib1)
        right = self.right.get_curve(cell.rib2)

        return left, right

    def get_mesh(self, cell: Cell, insert_points: int=10, project_3d: bool=False) -> mesh.Mesh:
        """
        get a mesh from a diagonal (2 poly lines)
        """
        left, right = self.get_3d(cell)
        left_2d, right_2d = self.get_flattened(cell)
        
        envelope_2d = left_2d.nodes
        envelope_3d = left.nodes


        def get_list_3d(p1: euklid.vector.Vector3D, p2: euklid.vector.Vector3D) -> list[euklid.vector.Vector3D]:
            return [
                p1 + (p2-p1) * ((i+1)/(insert_points+1))
                for i in range(insert_points)
            ]
        def get_list_2d(p1: euklid.vector.Vector2D, p2: euklid.vector.Vector2D) -> list[euklid.vector.Vector2D]:
            return [
                p1 + (p2-p1) * ((i+1)/(insert_points+1))
                for i in range(insert_points)
            ]

        envelope_2d += get_list_2d(left_2d.nodes[-1], right_2d.nodes[-1])
        envelope_3d += get_list_3d(left.nodes[-1], right.nodes[-1])

        envelope_2d += right_2d.reverse().nodes
        envelope_3d += right.reverse().nodes

        envelope_2d += get_list_2d(right_2d.nodes[0], left_2d.nodes[0])
        envelope_3d += get_list_3d(right.nodes[0], left.nodes[0])
        
        boundary_nodes = list(range(len(envelope_2d)))
        boundary = [boundary_nodes+[0]]
        
        tri = openglider.mesh.triangulate.Triangulation([(p[0], p[1]) for p in envelope_2d], boundary)
        tri_mesh = tri.triangulate()

        # map 2d-points to 3d-points

        # todo: node_no = kgv(len(left), len(right))
        node_no = 100

        mapping_2d = Mapping([right_2d.resample(node_no), left_2d.resample(node_no)])
        mapping_3d = Mapping3D([right.resample(node_no), left.resample(node_no)])

        points_3d: list[euklid.vector.Vector3D] = []

        for point_3d, point_2d in zip(envelope_3d, tri_mesh.points[:len(envelope_2d)]):
            vector_3d = euklid.vector.Vector3D(point_3d)
            points_3d.append(vector_3d)

        for point in tri_mesh.points[len(envelope_2d):]:
            ik = mapping_2d.get_iks(point)
            points_3d.append(mapping_3d.get_point(*ik))
        
        drib_mesh = mesh.Mesh.from_indexed(points_3d, {"diagonals": [(p, {}) for p in tri_mesh.elements]}, boundaries={"diagonals": boundary_nodes})

        min_size = drib_mesh.polygon_size()[0]
        if  min_size < 1e-20:
            raise Exception(f"min polygon size: {min_size} in drib: {self.name}")

        return drib_mesh

    def get_flattened(self, cell: Cell, ribs_flattened: Any=None) -> tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]:
        first, second = self.get_3d(cell)
        left, right = flatten_list(first, second)
        return left, right

    def get_average_x(self) -> Percentage:
        """
        return average x value for sorting
        """
        return (self.left.center + self.right.center)/2