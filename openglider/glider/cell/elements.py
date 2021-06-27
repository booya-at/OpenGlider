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
import copy
import logging
from typing import Tuple
import numpy as np
import math

import euklid

import openglider.vector
from openglider.airfoil import get_x_value
import openglider.mesh as mesh
from openglider.utils.cache import cached_function, hash_list
from openglider.vector.projection import flatten_list
from openglider.utils import Config


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from openglider.glider.cell import Cell

class DiagonalRib(object):
    def __init__(self, left_front, left_back, right_front, right_back, material_code="", name="unnamed"):
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

    def __json__(self):
        return {'left_front': self.left_front,
                'left_back': self.left_back,
                'right_front': self.right_front,
                'right_back': self.right_back,
                "material_code": self.material_code,
                "name": self.name
        }

    @property
    def width_left(self):
        return abs(self.left_front[0] - self.left_back[0])

    @property
    def width_right(self):
        return abs(self.right_front[0] - self.right_back[0])

    @property
    def center_left(self):
        return (self.left_front[0] + self.left_back[0])/2

    @property
    def center_right(self):
        return (self.right_front[0] + self.right_back[0])/2

    @width_left.setter
    def width_left(self, width):
        center = self.center_left
        self.left_front[0] = center - width/2
        self.left_back[0] = center + width/2

    @width_right.setter
    def width_right(self, width):
        center = self.center_right
        self.right_front[0] = center - width/2
        self.right_back[0] = center + width/2

    def copy(self):
        return copy.copy(self)

    def mirror(self):
        self.left_front, self.right_front = self.right_front, self.left_front
        self.left_back, self.right_back = self.right_back, self.left_back

    def get_center_length(self, cell):
        p1 = cell.rib1.point(self.center_left)
        p2 = cell.rib2.point(self.center_right)
        return (p2 - p1).length()

    def get_3d(self, cell):
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

    def get_mesh(self, cell, insert_points=4, project_3d=False):
        """
        get a mesh from a diagonal (2 poly lines)
        """
        left, right = self.get_3d(cell)

        if insert_points:
            point_array = []
            points2d = []
            number_array = []
            # create array of points
            # the outermost points build the segments
            num_left = len(left)
            num_right = len(right)
            count = 0

            for y_pos in np.linspace(0., 1., insert_points + 2):
                # from left to right
                line_points = []
                line_points_2d = []  # TODO: mesh 2d (x, y) -> 3d nodes
                line_indices = []
                num_points = int(num_left * (1. - y_pos) + num_right * y_pos)


                for x_pos in np.linspace(0., 1., num_points):
                    line_points.append(
                        left.get(x_pos * (num_left - 1)) * (1. - y_pos) +
                        right.get(x_pos * (num_right - 1)) * y_pos)
                    line_points_2d.append([x_pos, y_pos])
                    line_indices.append(count)
                    count += 1

                point_array += line_points
                points2d += line_points_2d
                number_array.append(line_indices)

            # outline
            edge = number_array[0]
            edge += [line[-1] for line in number_array[1:]]
            edge += number_array[-1][-2::-1]  # last line reversed without the last element
            edge += [line[0] for line in number_array[1:-1]][::-1]

            segment = [[edge[i], edge[i +1]] for i in range(len(edge) - 1)]
            segment.append([edge[-1], edge[0]])

            point_array = np.array(point_array)
            import openglider.mesh.mesh as _mesh

            if project_3d:
                points2d = _mesh.map_to_2d(point_array)

            tri = mesh.triangulate.Triangulation(points2d, [edge])
            tri.name = self.name

            tri_mesh = tri.triangulate(options="Qz")
            # mesh_info = _mesh.mptriangle.MeshInfo()
            # mesh_info.set_points(points2d)
            # mesh_info.set_facets(segment)
            # mesh = _mesh.custom_triangulation(mesh_info, "Qz")
            

            return mesh.Mesh.from_indexed(point_array, {"diagonals": list(tri_mesh.elements)}, boundaries={"diagonals": edge})

        else:
            vertices = np.array(list(left) + list(right)[::-1])
            polygon = [range(len(vertices))]
            return mesh.Mesh.from_indexed(vertices, {"diagonals": polygon})

    def get_flattened(self, cell, ribs_flattened=None):
        first, second = self.get_3d(cell)
        left, right = flatten_list(first, second)
        return left, right

    def get_average_x(self):
        """
        return average x value for sorting
        """
        return (self.left_front[0] + self.left_back[0] +
                self.right_back[0] + self.right_front[0]) / 4


class DoubleDiagonalRib(object):
    pass  # TODO


class TensionStrap(DiagonalRib):
    def __init__(self, left, right, width, height=-1, material_code="", name=""):
        """
        Similar to a Diagonalrib but always connected to the bottom-sail.
        :param left: left center of TensionStrap as x-value
        :param right: right center of TesnionStrap as x-value
        :param width: width of TensionStrap
        :param material_code: color/material-name (optional)
        :param name: name of TensionStrap (optional)
        """
        width /= 2
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
        super(TensionLine, self).__init__(left, right, 0.01, material_code=material_code, name=name)
        self.left = left
        self.right = right

    def __json__(self):
        return {"left": self.left,
                "right": self.right,
                "material_code": self.material_code,
                "name": self.name
            }

    def get_length(self, cell):
        rib1 = cell.rib1
        rib2 = cell.rib2
        left = rib1.profile_3d[rib1.profile_2d(self.left)]
        right = rib2.profile_3d[rib2.profile_2d(self.right)]

        return (left - right).length()

    def get_center_length(self, cell):
        return self.get_length(cell)

    def mirror(self):
        self.left, self.right = self.right, self.left

    def get_mesh(self, cell):
        boundaries = {}
        rib1 = cell.rib1
        rib2 = cell.rib2
        p1 = rib1.profile_3d[rib1.profile_2d(self.left)]
        p2 = rib2.profile_3d[rib2.profile_2d(self.right)]
        boundaries[rib1.name] = [0]
        boundaries[rib2.name] = [1]
        return mesh.Mesh.from_indexed([p1, p2], {"tension_lines": [[0, 1]]}, boundaries=boundaries)


class PanelCut(object):
    def __init__(self, left, right, style=0, is_3d=False):
        self.left = left
        self.right = right
        self.style = style
        self.is_3d = is_3d
        self.amount_3d = []

    def add_3d_amount(self, amount):
        self.amount_3d.append(amount)

    def get_3d_amount(self):
        if len(self.amount_3d) == 0:
            return 0

        return sum(self.amount_3d) / len(self.amount_3d)

    @property
    def mean_x(self):
        return (self.left + self.right) / 2




class Panel(object):
    """
    Glider cell-panel
    :param cut_front {'left': 0.06, 'right': 0.06, 'type': 'orthogonal'}
    """
    class CUT_TYPES(Config):
        """
        all available cut_types:
        - folded: start end of open panel (entry)
        - orthogonal: design cuts
        - singleskin-cut: start/end of a open singleskin-section (used for different rib-modifications)
        - 3d: 3d design cut
        """
        folded = "folded"
        orthogonal = "orthogonal"
        singleskin = "singleskin"
        cut_3d = "cut_3d"

    def __init__(self, cut_front, cut_back, material_code=None, name="unnamed"):
        self.cut_front = cut_front  # (left, right, style(int))
        self.cut_back = cut_back
        self.material_code = material_code or ""
        self.name = name

    def __json__(self):
        return {'cut_front': self.cut_front,
                'cut_back': self.cut_back,
                "material_code": self.material_code,
                "name": self.name
                }

    @classmethod
    def dummy(cls):
        return cls(
            {"left": -1, "right": -1, "type": "parallel"},
            {"left": 1, "right": 1, "type": "parallel"}
        )
    
    def __hash__(self) -> int:
        return hash_list(*self.cut_front.values(), *self.cut_back.values())

    def mean_x(self) -> float:
        """
        :return: center point of the panel as x-values
        """
        total = self.cut_front["left"]
        total += self.cut_front["right"]
        total += self.cut_back["left"]
        total += self.cut_back["right"]

        return total/4

    def __radd__(self, other):
        """needed for sum(panels)"""
        if not isinstance(other, Panel):
            return self

    def __add__(self, other):
        if self.cut_front == other.cut_back:
            return Panel(other.cut_front, self.cut_back, material_code=self.material_code)
        elif self.cut_back == other.cut_front:
            return Panel(self.cut_front, other.cut_back, material_code=self.material_code)
        else:
            return None

    def is_lower(self):
        return self.mean_x() > 0

    def get_3d(self, cell, numribs=0, midribs=None, with_numpy=False):
        """
        Get 3d-Panel
        :param glider: glider class
        :param numribs: number of miniribs to calculate
        :return: List of rib-pieces (Vectorlist)
        """
        xvalues = cell.rib1.profile_2d.x_values
        ribs = []
        for i in range(numribs + 1):
            y = i / numribs

            if midribs is None:
                midrib = cell.midrib(y, with_numpy)
            else:
                midrib = midribs[i]

            x1 = self.cut_front["left"] + y * (self.cut_front["right"] -
                                               self.cut_front["left"])
            front = get_x_value(xvalues, x1)

            x2 = self.cut_back["left"] + y * (self.cut_back["right"] -
                                              self.cut_back["left"])
            back = get_x_value(xvalues, x2)
            ribs.append(midrib.get(front, back))
            # todo: return polygon-data
        return ribs

    def get_mesh(self, cell, numribs=0, with_numpy=False, exact=False):
        """
        Get Panel-mesh
        :param cell: the parent cell of the panel
        :param numribs: number of interpolation steps between ribs
        :param with_numpy: compute midribs with numpy (faster if available)
        :return: mesh objects consisting of triangles and quadrangles
        """
        # TODO: doesn't work for numribs=0?
        
        xvalues = cell.rib1.profile_2d.x_values
        x_value_interpolation = euklid.vector.Interpolation([[i, x] for i, x in enumerate(xvalues)])

        rib_iks = []
        points = []
        rib_node_indices = []

        ik_values = self._get_ik_values(cell, numribs, exact=exact)

        for rib_no in range(numribs + 2):
            y = rib_no / max(numribs+1, 1)

            front, back = ik_values[rib_no]

            midrib = cell.midrib(y)

            rib_iks.append(midrib.get_positions(front, back))

            i0 = len(points)
            rib_node_indices.append([i + i0 for i, _ in enumerate(rib_iks[-1])])

            points += list(midrib.get(front, back))

        points = [mesh.Vertex(*p) for p in points]

        polygons = []

        # helper functions
        def left_triangle(l_i, r_i):
            return mesh.Polygon([points[l_i+1], points[l_i], points[r_i]])

        def right_triangle(l_i, r_i):
            return mesh.Polygon([points[r_i+1], points[l_i], points[r_i]])

        def quad(l_i, r_i):
            return mesh.Polygon([points[l_i+1], points[l_i], points[r_i], points[r_i+1]])

        for rib_no, _ in enumerate(rib_iks[:-1]):
            x = (2*rib_no+1) / (numribs+1) / 2
            indices_left = rib_node_indices[rib_no]
            indices_right = rib_node_indices[rib_no + 1]

            iks_left = rib_iks[rib_no]
            iks_right = rib_iks[rib_no + 1]
            l_i = r_i = 0

            while l_i < len(indices_left)-1 or r_i < len(indices_right)-1:
                if l_i == len(indices_left) - 1:
                    poly = right_triangle(indices_left[l_i], indices_right[r_i])
                    r_i += 1

                elif r_i == len(indices_right) - 1:
                    poly = left_triangle(indices_left[l_i], indices_right[r_i])
                    l_i += 1

                elif abs(iks_left[l_i] - iks_right[r_i]) == 0:
                    poly = quad(indices_left[l_i], indices_right[r_i])
                    r_i += 1
                    l_i += 1

                elif iks_left[l_i] <= iks_right[r_i]:
                    poly = left_triangle(indices_left[l_i], indices_right[r_i])
                    l_i += 1

                elif iks_right[r_i] < iks_left[l_i]:
                    poly = right_triangle(indices_left[l_i], indices_right[r_i])
                    r_i += 1

                # TODO: improve logic for triangles
                iks = [iks_left[l_i], iks_right[r_i]]
                if l_i < len(iks_left) - 1:
                    iks.append(iks_left[l_i+1])
                if r_i < len(iks_right) - 1:
                    iks.append(iks_right[r_i+1])
                
                poly.attributes["center"] = [x, x_value_interpolation.get_value(sum(iks)/len(iks))]
                polygons.append(poly)
        #connection_info = {cell.rib1: np.array(ribs[0], int),
        #                   cell.rib2: np.array(ribs[-1], int)}

        return mesh.Mesh({f"panel_{self.material_code}": polygons}, name=self.name)

    def mirror(self):
        """
        mirrors the cuts of the panel
        """
        front = self.cut_front
        self.cut_front.update({
            "right": front["left"],
            "left": front["right"]
        })
        back = self.cut_back
        self.cut_back.update({
            "right": back["left"],
            "left": back["right"]
        })
    
    def snap(self, cell):
        """
        replaces panel x_valus with x_values stored in profile-2d-x-values
        """
        p_l = cell.rib1.profile_2d
        p_r = cell.rib2.profile_2d
        self.cut_back["left"] = p_l.nearest_x_value(self.cut_back["left"])
        self.cut_back["right"] = p_r.nearest_x_value(self.cut_back["right"])
        self.cut_front["left"] = p_l.nearest_x_value(self.cut_front["left"])
        self.cut_front["right"] = p_r.nearest_x_value(self.cut_front["right"])

    @cached_function("self")
    def _get_ik_values(self, cell: "openglider.glider.cell.Cell", numribs=0, exact=True):
        """
        :param cell: the parent cell of the panel
        :param numribs: number of interpolation steps between ribs
        :return: [[front_ik_0, back_ik_0], ..[front_ik_n, back_ik_n]] with n is numribs + 1
        """
        # TODO: move to cut!!
        x_values_left = cell.rib1.profile_2d.x_values

        ik_left_front = get_x_value(x_values_left, self.cut_front["left"])
        ik_left_back = get_x_value(x_values_left, self.cut_back["left"])
        

        x_values_right = cell.rib2.profile_2d.x_values
        ik_right_front = get_x_value(x_values_right, self.cut_front["right"])
        ik_right_back = get_x_value(x_values_right, self.cut_back["right"])



        ik_values = [[ik_left_front, ik_left_back]]

        for i in range(numribs):
            y = float(i+1)/(numribs+1)

            front = ik_left_front + y * (ik_right_front - ik_left_front)
            back = ik_left_back + y * (ik_right_back - ik_left_back)

            ik_values.append([front, back])
        
        ik_values.append([ik_right_front, ik_right_back])

        if exact:
            ik_values_new = []
            inner = cell.get_flattened_cell(num_inner=numribs+2)["inner"]
            p_front_left = inner[0].get(ik_left_front)
            p_front_right = inner[-1].get(ik_right_front)
            p_back_left = inner[0].get(ik_left_back)
            p_back_right = inner[-1].get(ik_right_back)

            for i, ik in enumerate(ik_values):
                ik_front, ik_back = ik
                line: euklid.vector.PolyLine2D = inner[i]

                _ik_front, _ = line.cut(p_front_left, p_front_right, ik_front)
                if abs(_ik_front-ik_front) > 20:
                    _ik_front = ik_front
                _ik_back, _ = line.cut(p_back_left, p_back_right, ik_back)
                if abs(_ik_back-ik_back) > 20:
                    _ik_back = ik_back

                ik_values_new.append((_ik_front, _ik_back))
            
            nix = 1
            return ik_values_new
        
        else:
            return ik_values
        
    @cached_function("self")
    def _get_ik_interpolation(self, cell: "Cell", numribs=0, exact=True):
        ik_values = self._get_ik_values(cell, numribs=5, exact=exact)
        numpoints = len(ik_values)-1
        ik_interpolation_front = euklid.vector.Interpolation(
            [[i/numpoints, x[0]] for i, x in enumerate(ik_values)]
            )
        
        ik_interpolation_back = euklid.vector.Interpolation(
            [[i/numpoints, x[1]] for i, x in enumerate(ik_values)]
        )

        return ik_interpolation_front, ik_interpolation_back

    def integrate_3d_shaping(self, cell: "Cell", sigma, inner_2d, midribs=None):
        """
        :param cell: the parent cell of the panel
        :param sigma: std-deviation parameter of gaussian distribution used to weight the length differences.
        :param inner_2d: list of 2D polylines (flat representation of the cell)s
        :param midribs: precomputed midribs, None by default
        :return: front, back (lists of lengths) with length equal to number of midribs
        """
        numribs = len(inner_2d) - 2
        if midribs is None or len(midribs) != len(inner_2d):
            midribs = cell.get_midribs(numribs+2)

        #ribs = [cell.prof1] + midribs + [cell.prof2]
        ribs = midribs

        # ! vorn + hinten < gesamt !

        positions = self._get_ik_values(cell, numribs, exact=True)

        front = []
        back = []

        ff = math.sqrt(math.pi/2)*sigma

        for rib_no in range(numribs + 2):
            x1, x2 = positions[rib_no]
            rib_2d = inner_2d[rib_no].get(x1,x2)
            rib_3d = ribs[rib_no].get(x1, x2)

            lengthes_2d = rib_2d.get_segment_lengthes()
            lengthes_3d = rib_3d.get_segment_lengthes()

            distance = 0
            amount_front = 0
            # influence factor: e^-(x^2/(2*sigma^2))
            # -> sigma = einflussfaktor [m]
            # integral = sqrt(pi/2)*sigma * [ erf(x / (sqrt(2)*sigma) ) ]

            def integrate(lengths_2d, lengths_3d):
                amount = 0
                distance = 0

                for l2d, l3d in zip(lengths_2d, lengths_3d):
                    if l3d > 0:
                        factor = (l3d - l2d) / l3d
                        x = math.erf( (distance + l3d) / (sigma*math.sqrt(2))) - math.erf(distance / (sigma*math.sqrt(2)))

                        amount += factor * x
                    distance += l3d
            
                return amount

            amount_back = integrate(lengthes_2d, lengthes_3d)
            amount_front = integrate(lengthes_2d[::-1], lengthes_3d[::-1])

            for l2d, l3d in zip(lengthes_2d, lengthes_3d):
                if l3d > 0:
                    factor = (l3d - l2d) / l3d
                    x = math.erf( (distance + l3d) / (sigma*math.sqrt(2))) - math.erf(distance / (sigma*math.sqrt(2)))

                    amount_front += factor * x
                distance += l3d

            distance = 0
            amount_back = 0

            for l2d, l3d in zip(lengthes_2d[::-1], lengthes_3d[::-1]):
                if l3d > 0:
                    factor = (l3d - l2d) / l3d
                    x = math.erf( (distance + l3d) / (sigma*math.sqrt(2))) - math.erf(distance / (sigma*math.sqrt(2)))
                    amount_back += factor * x
                distance += l3d

            total = 0
            for l2d, l3d in zip(lengthes_2d, lengthes_3d):
                total += l3d - l2d


            amount_front *= ff
            amount_back *= ff

            if self.cut_front["type"] != "cut_3d" and self.cut_back["type"] != "cut_3d":
                if abs(amount_front + amount_back) > abs(total):
                    normalization = abs(total / (amount_front + amount_back))
                    amount_front *= normalization
                    amount_back *= normalization

            if rib_no == 0 or rib_no == numribs+1:
                amount_front = 0
                amount_back = 0
                
            front.append(amount_front)
            back.append(amount_back)

        return front, back


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
    
    def _get_flattened_line(self, cell):
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




    
