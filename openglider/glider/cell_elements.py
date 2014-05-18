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
    def __init__(self, (left_1, left_1_height), (left_2, left_2_height),
                 (right_1, right_1_height), (right_2, right_2_height), cell_no):
        # Attributes
        self.attributes = [[[left_1, left_1_height], [left_2, left_2_height]],
                           [[right_1, right_1_height], [right_2, right_2_height]]]
        self.cell = cell_no

    def get_3d(self, glider):
        """
        Get 3d-Points of a diagonal rib
        :param glider: glider instance
        :return: (left_list, right_list)
        """
        cell = glider.cells[self.cell]
        # cell = openglider.glider.cells.Cell()
        lists = []
        for i, attributes in enumerate(self.attributes):
            rib = cell.ribs[i]
            points = [rib.profile_2d.profilepoint(x, h) for x, h in attributes]
            if attributes[0][1] == attributes[1][1] == -1:
                #print(points)
                lists.append(rib.profile_3d.get(points[0][0], points[1][0]))
            else:
                lists.append([rib.align([p[0], p[1], 0]) for p in points])
        return lists

    def get_flattened(self, glider, ribs_flattened):
        first, second = self.get_3d(glider)
        left, right = flatten_list(first, second)
        return left, right
        # Insert Marks into ribs
        # ribs_flattened[self.cell]
        # ribs_flattened[self.cell+1]


class DoubleDiagonalRib():
    pass


class TensionStrapSimple(DiagonalRib):
    def __init__(self, left, right, width, cell_no):
        super(TensionStrapSimple, self).__init__((left - width, 0), (left + width, 0),
                                                 (right - width, 0), (right + width, 0), cell_no)

    def get_flattened(self, glider, ribs_flattened):
        ## Draw signs into airfoil (just one)

        ## Return Length

        pass


class Panel(object):
    """
    Glider cell-panel
    """
    def __init__(self, cut_front, cut_back, cell_no):
        self.cut_front = cut_front  # (left, right, style(int))
        self.cut_back = cut_back
        self.cell_no = cell_no
        # TODO: colour, material, ..

    def get_3d(self, glider, numribs=0):
        """
        Get 3d-Panel
        :param glider: glider class
        :param numribs: number of miniribs to calculate
        :return: List of rib-pieces (Vectorlist)
        """
        cell = glider.cells[self.cell_no]
        xvalues = glider.x_values
        numribs += 1
        ribs = []
        for i in range(numribs):
            y = i / numribs
            front = get_x_value(xvalues, self.cut_front[0] + y * (self.cut_front[1] - self.cut_front[0]))
            back = get_x_value(xvalues, self.cut_back[0] + y * (self.cut_back[1] - self.cut_back[0]))
            ribs.append(cell.midrib(y).get(front, back))
            # todo: return polygon-data
        return ribs

    def get_flattened(self, glider):
        cell = glider.cells[self.cell_no]









