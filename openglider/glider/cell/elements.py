import copy
import logging
import math
from typing import TYPE_CHECKING, List, Tuple

import euklid
import numpy as np
import openglider.jsonify
import openglider.mesh as mesh
import openglider.vector
from openglider.airfoil import get_x_value
from openglider.materials import Material, cloth
from openglider.utils.cache import cached_function, hash_list
from openglider.utils.config import Config
from openglider.vector.mapping import Mapping, Mapping3D
from openglider.vector.projection import flatten_list

if TYPE_CHECKING:
    from openglider.glider.cell import Cell

logger = logging.getLogger(__name__)

class DiagonalRib(object):
    hole_num = 0
    hole_border_side = 0.15
    hole_border_front_back = 0.1

    def __init__(self, left_front, left_back, right_front, right_back, num_folds=1, material_code="", name="unnamed"):
        """
        [left_front, left_back, right_front, right_back]
        -> Cut: (x_value, height)
        :param left_front as x-value
        :param left_back as x-value
        :param right_front as x-value
        :param right_back as x-value
        :param material_code: color/material (optional)
        :param name: optional name of DiagonalRib (optional)
        """
        # Attributes
        self.left_front = left_front
        self.left_back = left_back
        self.right_front = right_front
        self.right_back = right_back
        self.material_code = material_code
        self.name = name
        self.num_folds = num_folds

    def __json__(self):
        return {'left_front': self.left_front,
                'left_back': self.left_back,
                'right_front': self.right_front,
                'right_back': self.right_back,
                "material_code": self.material_code,
                "name": self.name
        }

    @property
    def width_left(self) -> float:
        return abs(self.left_front[0] - self.left_back[0])

    @width_left.setter
    def width_left(self, width: float):
        center = self.center_left
        self.left_front[0] = center - width/2
        self.left_back[0] = center + width/2

    @property
    def width_right(self) -> float:
        return abs(self.right_front[0] - self.right_back[0])

    @width_right.setter
    def width_right(self, width: float):
        center = self.center_right
        self.right_front[0] = center - width/2
        self.right_back[0] = center + width/2

    @property
    def center_left(self) -> float:
        return (self.left_front[0] + self.left_back[0])/2

    @property
    def center_right(self) -> float:
        return (self.right_front[0] + self.right_back[0])/2

    def copy(self):
        return copy.copy(self)

    def mirror(self) -> None:
        self.left_front, self.right_front = self.right_front, self.left_front
        self.left_back, self.right_back = self.right_back, self.left_back

    def get_center_length(self, cell) -> float:
        p1 = cell.rib1.point(self.center_left)
        p2 = cell.rib2.point(self.center_right)
        return (p2 - p1).length()

    def get_3d(self, cell) -> Tuple[euklid.vector.PolyLine3D, euklid.vector.PolyLine3D]:
        """
        Get 3d-Points of a diagonal rib
        :return: (left_list, right_list)
        """

        def get_list(rib, cut_front, cut_back):
            # Is it at 0 or 1?
            if cut_back[1] == cut_front[1] and cut_front[1] in (-1, 1):
                side = -cut_front[1]  # -1 -> lower, 1->upper
                front = rib.profile_2d(cut_front[0] * side)
                back = rib.profile_2d(cut_back[0] * side)

                poly2 = rib.profile_3d.curve

                return poly2.get(front, back)
                #return euklid.vector.PolyLine3D(rib.profile_3d[front:back].data.tolist())
            else:
                return euklid.vector.PolyLine3D([rib.align(rib.profile_2d.align(p)) for p in (cut_front, cut_back)])

        left = get_list(cell.rib1, self.left_front, self.left_back)
        right = get_list(cell.rib2, self.right_front, self.right_back)

        return left, right

    def get_mesh(self, cell, insert_points=10, project_3d=False) -> mesh.Mesh:
        """
        get a mesh from a diagonal (2 poly lines)
        """
        left, right = self.get_3d(cell)
        left_2d, right_2d = self.get_flattened(cell)
        
        envelope_2d = left_2d.tolist()
        envelope_3d = left.tolist()


        def get_list(p1, p2):
            return [
                list(p1 + (p2-p1) * ((i+1)/(insert_points+1)))
                for i in range(insert_points)
            ]

        envelope_2d += get_list(left_2d.nodes[-1], right_2d.nodes[-1])
        envelope_3d += get_list(left.nodes[-1], right.nodes[-1])

        envelope_2d += right_2d.reverse().tolist()
        envelope_3d += right.reverse().tolist()

        envelope_2d += get_list(right_2d.nodes[0], left_2d.nodes[0])
        envelope_3d += get_list(right.nodes[0], left.nodes[0])
        
        boundary_nodes = list(range(len(envelope_2d)))
        boundary = [boundary_nodes+[0]]
        
        holes, hole_centers = self.get_holes(cell)
        
        for curve in holes:
            start_index = len(envelope_2d)
            hole_vertices = curve.tolist()[:-1]
            hole_indices = list(range(len(hole_vertices))) + [0]
            envelope_2d += hole_vertices
            boundary.append([start_index + i for i in hole_indices])

        hole_centers_lst = [list(p) for p in hole_centers]

        tri = mesh.triangulate.Triangulation(envelope_2d, boundary, hole_centers_lst)
        tri_mesh = tri.triangulate()

        # map 2d-points to 3d-points

        # todo: node_no = kgv(len(left), len(right))
        node_no = 100

        mapping_2d = Mapping([right_2d.resample(node_no), left_2d.resample(node_no)])
        mapping_3d = Mapping3D([right.resample(node_no), left.resample(node_no)])

        points_3d: List[euklid.vector.Vector3D] = []

        for point_3d, point_2d in zip(envelope_3d, tri_mesh.points[:len(envelope_2d)]):
            vector_3d = euklid.vector.Vector3D(point_3d)
            points_3d.append(vector_3d)

        for point in tri_mesh.points[len(envelope_2d):]:
            ik = mapping_2d.get_iks(euklid.vector.Vector2D(point))
            points_3d.append(mapping_3d.get_point(*ik))
        
        drib_mesh = mesh.Mesh.from_indexed(points_3d, {"diagonals": list(tri_mesh.elements)}, boundaries={"diagonals": boundary_nodes})

        min_size = drib_mesh.polygon_size()[0]
        if  min_size < 1e-20:
            raise Exception(f"min polygon size: {min_size} in drib: {self.name}")

        return drib_mesh


    def get_holes(self, cell, points=40) -> Tuple[List[euklid.vector.PolyLine2D], List[euklid.vector.Vector2D]]:
        left, right = self.get_flattened(cell)

        len_left = left.get_length()
        len_right = right.get_length()

        def get_point(x, y):
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

    def get_flattened(self, cell, ribs_flattened=None) -> Tuple[euklid.vector.PolyLine2D, euklid.vector.PolyLine2D]:
        first, second = self.get_3d(cell)
        left, right = flatten_list(first, second)
        return left, right

    def get_average_x(self) -> float:
        """
        return average x value for sorting
        """
        return (self.left_front[0] + self.left_back[0] +
                self.right_back[0] + self.right_front[0]) / 4


class DoubleDiagonalRib(object):
    pass  # TODO


class TensionStrap(DiagonalRib):
    hole_num = 0

    def __init__(self, left, right, width, height=-1, material_code="", name=""):
        """
        Similar to a Diagonalrib but always connected to the bottom-sail.
        :param left: left center of TensionStrap as x-value
        :param right: right center of TesnionStrap as x-value
        :param width: width of TensionStrap
        :param material_code: color/material-name (optional)
        :param name: name of TensionStrap (optional)
        """
        super(TensionStrap, self).__init__((left - width / 2, height),
                                           (left + width / 2, height),
                                           (right - width / 2, height),
                                           (right + width / 2, height),
                                           material_code,
                                           name)
    
    def __json__(self):
        return {
            "left": self.center_left,
            "right": self.center_right,
            "width": (self.width_left + self.width_right)/2,
            "height": self.left_front[1]
        }

class TensionLine(TensionStrap):
    def __init__(self, left, right, material_code="", name=""):
        """
        Similar to a TensionStrap but with fixed width (0.01)
        :param left: left center of TensionStrap as x-value
        :param right: right center of TesnionStrap as x-value
        :param material_code: color/material-name
        :param name: optional argument names
        """
        super().__init__(left, right, 0.01, material_code=material_code, name=name)
        self.left = left
        self.right = right

    def __json__(self):
        return {"left": self.left,
                "right": self.right,
                "material_code": self.material_code,
                "name": self.name
            }

    def get_length(self, cell) -> float:
        rib1 = cell.rib1
        rib2 = cell.rib2
        left = rib1.profile_3d[rib1.profile_2d(self.left)]
        right = rib2.profile_3d[rib2.profile_2d(self.right)]

        return (left - right).length()

    def get_center_length(self, cell) -> float:
        return self.get_length(cell)

    def mirror(self):
        self.left, self.right = self.right, self.left

    def get_mesh(self, cell, insert_points=10, project_3d=False) -> mesh.Mesh:
        boundaries = {}
        rib1 = cell.rib1
        rib2 = cell.rib2
        p1 = rib1.profile_3d[rib1.profile_2d(self.left)]
        p2 = rib2.profile_3d[rib2.profile_2d(self.right)]
        boundaries[rib1.name] = [0]
        boundaries[rib2.name] = [1]
        return mesh.Mesh.from_indexed([p1, p2], {"tension_lines": [[0, 1]]}, boundaries=boundaries)


class PanelRigidFoil():
    channel_width = 0.01
    def __init__(self, x_start: float, x_end: float, y: float=0.5):
        self.x_start = x_start
        self.x_end = x_end
        self.y = y
    
    def __json__(self):
        return {
            "x_start": self.x_start,
            "x_end": self.x_end,
            "y": self.y
        }
    
    def get_length(self, cell):
        line, start, end = self._get_flattened_line(cell)

        return line.get(start, end).get_length()
    
    def _get_flattened_line(self, cell) -> Tuple[euklid.vector.PolyLine2D, float, float]:
        flattened_cell = cell.get_flattened_cell()
        left, right = flattened_cell["ballooned"]
        line = left.mix(right, self.y)

        ik_front = (cell.rib1.profile_2d(self.x_start) + cell.rib2.profile_2d(self.x_start))/2
        ik_back = (cell.rib1.profile_2d(self.x_end) + cell.rib2.profile_2d(self.x_end))/2

        return line, ik_front, ik_back

    def draw_panel_marks(self, cell, panel):
        line, ik_front, ik_back = self._get_flattened_line(cell)

        #ik_values = panel._get_ik_values(cell, numribs=5)
        ik_interpolation_front, ik_interpolation_back = panel._get_ik_interpolation(cell, numribs=5)

        start = max(ik_front, ik_interpolation_front.get_value(self.y))
        stop = min(ik_back, ik_interpolation_back.get_value(self.y))

        if start < stop:
            return line.get(start, stop)
        
        return None

    def get_flattened(self, cell):
        line, ik_front, ik_back = self._get_flattened_line(cell)

        left = line.offset(-self.channel_width/2)
        right = line.offset(self.channel_width/2)

        contour = left.get(ik_front, ik_back) + right.get(ik_back, ik_front)

        # todo!
        #contour.close()

        marks = []

        panel_iks = []
        for panel in cell.panels:
            interpolations = panel._get_ik_interpolation(cell, numribs=5)

            panel_iks.append(interpolations[0].get_value(self.y))
            panel_iks.append(interpolations[1].get_value(self.y))
        
        for ik in panel_iks:
            if ik_front < ik < ik_back:
                marks.append(euklid.vector.PolyLine2D([
                    left.get(ik), right.get(ik)
                ]))

        return openglider.vector.drawing.PlotPart(
            cuts=[contour],
            marks=marks
        )




    
