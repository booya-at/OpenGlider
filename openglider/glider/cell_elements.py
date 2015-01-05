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

from openglider.airfoil import get_x_value
from openglider.plots.projection import flatten_list


class DiagonalRib(object):
    def __init__(self, left_1, left_2, right_1, right_2, rib1, rib2):
        # Attributes
        self.attributes = [[left_1, left_2],  # front (x,h) / back (x,h)
                           [right_1, right_2]]
        self.rib1 = rib1
        self.rib2 = rib2

    def __json__(self):
        return {'left_1': self.attributes[0][0],
                'left_2': self.attributes[0][1],
                'right_1': self.attributes[1][0],
                'right_2': self.attributes[1][1],
                'rib1': self.rib1,
                'rib2': self.rib2}


    def get_3d(self):
        """
        Get 3d-Points of a diagonal rib
        :return: (left_list, right_list)
        """
        # cell = openglider.glider.cells.Cell()

        def get_list(rib, cut_front, cut_back):
            if cut_back[1] == cut_front[1] and cut_front[1] in (-1, 1):
                side = -cut_front[1]  # -1 -> lower, 1->upper
                front = rib.profile_2d(cut_front[0] * side)
                back = rib.profile_2d(cut_back[0] * side)
                return rib.profile_3d[front:back]
            else:
                return [rib.align(p + [0]) for p in (cut_front, cut_back)]

        left = get_list(self.rib1, *self.attributes[0])
        right = get_list(self.rib1, *self.attributes[1])

        return left, right

    def get_flattened(self, ribs_flattened):
        first, second = self.get_3d()
        left, right = flatten_list(first, second)
        return left, right
        # Insert Marks into ribs
        # ribs_flattened[self.cell]
        # ribs_flattened[self.cell+1]


class DoubleDiagonalRib():
    pass


class TensionStrapSimple(DiagonalRib):
    def __init__(self, left, right, width, cell_no):
        width /= 2
        super(TensionStrapSimple, self).__init__((left - width, -1),
                                                 (left + width, -1),
                                                 (right - width, -1),
                                                 (right + width, -1), cell_no)

    def get_flattened(self, glider, ribs_flattened):
        ## Draw signs into airfoil (just one)

        ## Return Length

        pass


class Panel(object):
    """
    Glider cell-panel
    """

    def __init__(self, cut_front, cut_back, cell):
        self.cut_front = cut_front  # (left, right, style(int))
        self.cut_back = cut_back
        self.cell = cell
        # TODO: colour, material, ..

    def __json__(self):
        return {'cut_front': self.cut_front,
                'cut_back': self.cut_back,
                'cell': self.cell}

    def get_3d(self, glider, numribs=0):
        """
        Get 3d-Panel
        :param glider: glider class
        :param numribs: number of miniribs to calculate
        :return: List of rib-pieces (Vectorlist)
        """
        xvalues = glider.profile_x_values
        ribs = []
        for i in range(numribs + 1):
            y = i / numribs
            front = get_x_value(xvalues, self.cut_front[0] + y * (
                self.cut_front[1] - self.cut_front[0]))
            back = get_x_value(xvalues, self.cut_back[0] + y * (
                self.cut_back[1] - self.cut_back[0]))
            ribs.append(self.cell.midrib(y).get(front, back))
            # todo: return polygon-data
        return ribs

    def get_flattened(self, glider):
        pass









