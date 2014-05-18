# ! /usr/bin/python2
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
#from openglider.graphics import Graphics3D, Line, Graphics
from openglider.airfoil import get_x_value

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
        diff = right[i] - left[i]
        left_bal.data[i] -= diff * ballooning_left[i]
        right_bal.data[i] += diff * ballooning_right[i]
    return left_bal, left, right, right_bal


def flatten_glider(glider):
    assert isinstance(glider, openglider.Glider)
    # Temporary declarations:
    allowance_general = 0.01
    parts = []
    xvalues = glider.x_values

    for cell in glider.cells:
        left_bal, left, right, right_bal = flattened_cell(cell)
        left_out = left_bal.copy()
        right_out = right_bal.copy()
        left_out.add_stuff(-allowance_general)
        right_out.add_stuff(allowance_general)

        for panel in cell.panels:
            front_left = get_x_value(xvalues, panel.cut_front[0])
            back_left = get_x_value(xvalues, panel.cut_back[0])
            front_right = get_x_value(xvalues, panel.cut_front[1])
            back_right = get_x_value(xvalues, panel.cut_back[1])
            cut_front = cuts[panel.cut_front[2] - 1]([[left_bal, front_left],
                                                      [right_bal, front_right]],
                                                     left_out, right_out, -panel.cut_front[3])
            cut_back = cuts[panel.cut_back[2] - 1]([[left_bal, back_left],
                                                    [right_bal, back_right]],
                                                   left_out, right_out, panel.cut_back[3])
            parts.append(PlotPart({"OUTER_CUTS": [left_out[cut_front[1]:cut_back[1]] +
                                                  Vectorlist2D(cut_back[0]) +
                                                  right_out[cut_front[2]:cut_back[2]:-1] +
                                                  Vectorlist2D(cut_front[0])[::-1]],
                                   "SEWING_MARKS": [left_bal[front_left:back_left] +
                                                    right_bal[front_right:back_right:-1] +
                                                    Vectorlist2D([left_bal[front_left]])]}))

    for i, rib in enumerate(glider.ribs[:-1]):
        profile = rib.profile_2d.copy()
        profile_outer = profile.copy()
        profile_outer.add_stuff(0.01)
        profile_outer.close()
        chord = rib.chord
        attachment_points = filter(lambda p: p.rib_no==i, glider.attachment_points)

        profile_outer.scale(chord)
        profile.scale(chord)

        parts.append(PlotPart({"OUTER_CUTS": [profile_outer],
                      "SEWING_MARKS": [profile]}))



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
        max_x = lambda thalist: max(thalist, key=lambda point: point[0])[0]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def max_y(self):
        max_x = lambda thalist: max(thalist, key=lambda point: point[1])[1]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def min_x(self):
        max_x = lambda thalist: min(thalist, key=lambda point: point[0])[0]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    @property
    def min_y(self):
        max_x = lambda thalist: min(thalist, key=lambda point: point[1])[1]
        return max(map(lambda layer: max(map(max_x, layer)), self.layer_dict.itervalues()))

    def rotate(self, angle):
        for layer in self.layer_dict.itervalues():
            layer.rotate(angle)

    def shift(self, vector):
        for layer in self.layer_dict.itervalues():
            for vectorlist in layer:
                vectorlist.shift(vector)

    def return_layer_svg(self, layer):
        """
        Return a layer scaled for svg_coordinate_system [x,y = (mm, -mm)]
        """
        if layer in self.layer_dict:
            new = []
            for line in self.layer_dict[layer]:
                new.append(map(lambda point: point * [1000, -1000], line))
            return new
        else:
            return None


def create_svg(partlist, path):
    drawing = svgwrite.Drawing()
    #partlist = [partlist[1]]
    max_last = [0, 0]
    for part in partlist:
        part_group = svgwrite.container.Group()
        if "OUTER_CUTS" in part.layer_dict:
            part.shift([max_last[0] - part.min_x + 0.2, max_last[1] - part.min_y])
            max_last[0] = part.max_x
            #lines = part.return_layer_svg("SEWING_MARKS")
            lines = part.return_layer_svg("SEWING_MARKS")
            for line in lines:
                element = svgwrite.shapes.Polyline(line, id='outer',
                                                   stroke_width="1",
                                                   stroke="green",
                                                   fill="none")
                part_group.add(element)
            lines = part.return_layer_svg("OUTER_CUTS")
            for line in lines:
                element = svgwrite.shapes.Polyline(line, id='outer',
                                                   stroke_width="1",
                                                   stroke="black",
                                                   fill="none")
                part_group.add(element)
            drawing.add(part_group)

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
