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
from __future__ import division
import copy
import numpy

from openglider.airfoil import get_x_value
from openglider.plots.projection import flatten_list
from openglider.vector import norm
from openglider.mesh import Mesh


class DiagonalRib(object):
    def __init__(self, left_front, left_back, right_front, right_back, material_code="", name="unnamed"):
        """
        [left_front, left_back, right_front, right_back]
            -> Cut: (x_value, height)
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
                "material_code": self.material_code
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
                return rib.profile_3d[front:back]
            else:

                return [rib.align(rib.profile_2d.align(p) + [0]) for p in (cut_front, cut_back)]

        left = get_list(cell.rib1, self.left_front, self.left_back)
        right = get_list(cell.rib2, self.right_front, self.right_back)

        return left, right

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
    def __init__(self, left, right, width, material_code=None, name=""):
        width /= 2
        super(TensionStrap, self).__init__((left - width, -1),
                                           (left + width, -1),
                                           (right - width, -1),
                                           (right + width, -1),
                                           material_code,
                                           name)


class TensionStrapSimple(object):
    def __init__(self, left, right, material_code="", name=""):
        self.left = left
        self.right = right
        self.name = name
        self.material_code = material_code

    def __json__(self):
        return {"left": self.left,
                "right": self.right,
                "material_code": self.material_code}

    def get_length(self, cell):
        rib1 = cell.rib1
        rib2 = cell.rib2
        left = rib1.profile_3d[rib1.profile_2d(self.left)]
        right = rib2.profile_3d[rib2.profile_2d(self.right)]

        return norm(left - right)

    def mirror(self):
        self.left, self.right = self.right, self.left

    def get_3d(self, cell):
        rib1 = cell.rib1
        rib2 = cell.rib2
        left = rib1.profile_3d[rib1.profile_2d(self.left)]
        right = rib2.profile_3d[rib2.profile_2d(self.right)]
        return [left, right]


class Panel(object):
    """
    Glider cell-panel
    :param cut_front {'left': 0.06, 'right': 0.06, 'type': 'orthogonal'}
    """
    class CUT_TYPES:
        folded = "folded"
        orthogonal = "orthogonal"

    def __init__(self, cut_front, cut_back, material_code=None, name="unnamed"):
        self.cut_front = cut_front  # (left, right, style(int))
        self.cut_back = cut_back
        self.material_code = material_code or ""
        self.name = name

    def __json__(self):
        return {'cut_front': self.cut_front,
                'cut_back': self.cut_back,
                "material_code": self.material_code
                }

    def get_3d(self, cell, numribs=0):
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
            x1 = self.cut_front["left"] + y * (self.cut_front["right"] -
                                               self.cut_front["left"])
            front = get_x_value(xvalues, x1)

            x2 = self.cut_back["left"] + y * (self.cut_back["right"] -
                                              self.cut_back["left"])
            back = get_x_value(xvalues, x2)
            ribs.append(cell.midrib(y).get(front, back))
            # todo: return polygon-data
        return ribs

    def get_mesh(self, cell, numribs=0, with_numpy=True):
        """
        Get Panel-mesh
        :param cell: cell from which the panel-mesh is build
        :param numribs: number of miniribs to calculate
        :return: mesh
        """
        numribs += 1
        # TODO: doesnt work for numribs=0?
        xvalues = cell.rib1.profile_2d.x_values
        ribs = []
        points = []
        nums = []
        count = 0
        for rib_no in range(numribs + 1):
            y = rib_no / max(numribs, 1)
            x1 = self.cut_front["left"] + y * (self.cut_front["right"] -
                                               self.cut_front["left"])
            front = get_x_value(xvalues, x1)

            x2 = self.cut_back["left"] + y * (self.cut_back["right"] -
                                              self.cut_back["left"])
            back = get_x_value(xvalues, x2)
            midrib = cell.midrib(y, with_numpy=with_numpy)
            ribs.append([x for x in midrib.get_positions(front, back)])
            points += list(midrib[front:back])
            nums.append([i + count for i, _ in enumerate(ribs[-1])])
            count += len(ribs[-1])

        triangles = []

        def left_triangle(l_i, r_i):
            return [l_i + 1, l_i, r_i]

        def right_triangle(l_i, r_i):
            return [r_i + 1, l_i, r_i]

        def quad(l_i, r_i):
            return [l_i + 1, l_i, r_i, r_i + 1]

        for rib_no, _ in enumerate(ribs[:-1]):
            num_l = nums[rib_no]
            num_r = nums[rib_no + 1]
            pos_l = ribs[rib_no]
            pos_r = ribs[rib_no + 1]
            l_i = r_i = 0
            while l_i < len(num_l)-1 or r_i < len(num_r)-1:
                if l_i == len(num_l) - 1:
                    triangles.append(right_triangle(num_l[l_i], num_r[r_i]))
                    r_i += 1

                elif r_i == len(num_r) - 1:
                    triangles.append(left_triangle(num_l[l_i], num_r[r_i]))
                    l_i += 1

                elif abs(pos_l[l_i] - pos_r[r_i]) == 0:
                    triangles.append(quad(num_l[l_i], num_r[r_i]))
                    r_i += 1
                    l_i += 1

                elif pos_l[l_i] <= pos_r[r_i]:
                    triangles.append(left_triangle(num_l[l_i], num_r[r_i]))
                    l_i += 1

                elif pos_r[r_i] < pos_l[l_i]:
                    triangles.append(right_triangle(num_l[l_i], num_r[r_i]))
                    r_i += 1
        #connection_info = {cell.rib1: numpy.array(ribs[0], int),
        #                   cell.rib2: numpy.array(ribs[-1], int)}
        return Mesh.from_indexed(points, {"panel_"+self.material_code: triangles}, name=self.name)

    def mirror(self):
        left, right = self.cut_front["left"], self.cut_front["right"]
        self.cut_front["left"], self.cut_front["right"] = right, left

        left, right = self.cut_back["left"], self.cut_back["right"]
        self.cut_back["left"], self.cut_back["right"] = right, left

    def _get_ik_values(self, cell, numribs=0):
        x_values = cell.rib1.profile_2d.x_values
        ik_values = []

        for i in range(numribs+1):
            y = i/numribs
            x_front = self.cut_front["left"] + y * (self.cut_front["right"] -
                                                    self.cut_front["left"])

            x_back = self.cut_back["left"] + y * (self.cut_back["right"] -
                                                  self.cut_back["left"])

            front = get_x_value(x_values, x_front)
            back = get_x_value(x_values, x_back)

            ik_values.append([front, back])

        return ik_values

    def integrate_3d_shaping(self, cell, inner_2d, midribs=None):
        numribs = len(inner_2d) - 2
        if midribs is None:
            midribs = cell.get_midribs(numribs)

        ribs_3d = self.get_3d(cell, numribs, midribs)
        positions = self._get_ik_values(cell, numribs)
        ribs_2d = []

        for inner_rib, positions in zip(inner_2d, positions):
            ribs_2d.append(inner_rib.get(*positions))

        # influence factor: e^-(x/stofffaktor)
        # integral(x1, x2, e^-x) = -e^-x1 + e^-x2
        lengthes_3d = [rib.get_segment_lengthes() for rib in ribs_3d]
        lengthes_2d = [rib.get_segment_lengthes() for rib in ribs_2d]
        lengthes_diff = [l3 - l2 for l3, l2 in zip(lengthes_3d, lengthes_2d)]
