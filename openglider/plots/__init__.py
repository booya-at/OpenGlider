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
from dxfwrite import DXFEngine as dxf, DXFList
import numpy
import svgwrite
from openglider.graphics import Graphics3D, Line, Graphics

import openglider.plots.projection
from openglider.glider.cell import Cell
from .cuts import cuts
from openglider.vector import Vectorlist2D


def flattened_cell(cell):
    assert isinstance(cell, openglider.glider.Cell)
    left, right = openglider.plots.projection.flatten_list(cell.prof1, cell.prof2)
    left_bal = left.copy()
    right_bal = right.copy()
    ballooning_left = [cell.rib1.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    ballooning_right = [cell.rib2.ballooning[x] for x in cell.rib2.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i]-left[i]
        left_bal.data[i] -= diff * ballooning_left[i]
        right_bal.data[i] += diff * ballooning_right[i]
    return left_bal, left, right, right_bal


def flatten_glider(glider):
    assert isinstance(glider, openglider.Glider)
    # Temporary declarations:
    allowance_general = 0.01
    parts = []

    for cell in glider.cells:
        left_bal, left, right, right_bal = flattened_cell(cell)
        left_out = left.copy()
        right_out = right.copy()
        left_out.add_stuff(-allowance_general)
        right_out.add_stuff(allowance_general)
        parts.append(PlotPart({"OUTER_CUTS": [left_out + right_out[::-1]], "SEWING_MARKS": [left + right[::-1]]}))
    return parts


class PlotPart():
    def __init__(self, layer_dict=None):
        self._layer_dict = {}
        self.layer_dict = layer_dict or {}

    @property
    def layer_dict(self):
        return self._layer_dict

    @layer_dict.setter
    def layer_dict(self, layer_dict):
        assert isinstance(layer_dict, dict)
        for layer in layer_dict.iteritems():
            if not isinstance(layer, Vectorlist2D):
                layer = Vectorlist2D(layer)
        self._layer_dict = layer_dict

    def __getitem__(self, item):
        return self.layer_dict[item]

    @property
    def max_x(self):
        return max(map(lambda layer: max(map(lambda point: point[0], layer)), self.layer_dict))

    @property
    def max_y(self):
        return max(map(lambda layer: max(map(lambda point: point[0], layer)), self.layer_dict))

    @property
    def min_x(self):
        return min(map(lambda layer: min(map(lambda point: point[0], layer)), self.layer_dict))

    @property
    def min_y(self):
        return min(map(lambda layer: min(map(lambda point: point[0], layer)), self.layer_dict))

    def rotate(self, angle):
        for layer in self.layer_dict.itervalues():
            layer.rotate(angle)

    def shift(self, vector):
        for layer in self.layer_dict.itervalues():
            layer.shift(vector)



def create_svg(partlist, path):
    drawing = svgwrite.Drawing()
    partlist = [partlist[1]]
    for part in partlist:
        if "OUTER_CUTS" in part.layer_dict:
            lines = part["SEWING_MARKS"]
            for line in lines:
                element = svgwrite.shapes.Polyline(line, id='outer',
                                                   stroke_width="0.002",
                                                   stroke="black",
                                                   fill="none")
                element.scale(1000)
                drawing.add(element)

    with open(path, "w") as output_file:
        return drawing.write(output_file)

# FLATTENING
# Dict for layers
# Flatten all cell-parts
#   * attachment points
#   * miniribs
#   * sewing marks
# FLATTEN RIBS
#   * airfoil
#   * attachment points
#   * gibus arcs
#   * holes
#   * rigidfoils
#   * sewing marks
#   ---> SCALE
# FLATTEN DIAGONALS
#     * Flatten + add stuff
#     * Draw marks on ribs
