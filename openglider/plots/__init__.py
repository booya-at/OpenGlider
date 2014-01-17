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
import math
#import svgwrite
from dxfwrite import DXFEngine as dxf, DXFList
import openglider.Cells
import openglider
import openglider.Vector
import openglider.Vector.projection


def flattened_cell(cell=openglider.Cells.Cell()):
    left, right = openglider.Vector.projection.flatten_list(cell.rib1.profile_3d, cell.rib2.profile_3d)
    ballooning_left = [cell.rib1.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    ballooning_right = [cell.rib2.ballooning[x] for x in cell.rib2.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i]-left[i]
        left.data[i] -= diff * ballooning_left[i]
        right.data[i] += diff * ballooning_right[i]
    return left, right


def flatten_glider(glider, path):
    # Temporary declarations:
    allowance_general = 0.01
    glider.recalc()
    parts = []

    drawing = dxf.drawing(path)
    drawing.add_layer('MARKS')
    drawing.add_layer('CUTS')

    for cell in glider.cells:
        left, right = flattened_cell(cell)

        left_out = left.copy()
        right_out = right.copy()
        left_out.add_stuff(-allowance_general)
        right_out.add_stuff(allowance_general)

        right_out.data = right_out.data[::-1]
        left_out += right_out
        right.data = right.data[::-1]
        left = left + right

        left.layer = 'MARKS'
        left_out.layer = 'CUTS'

        parts.append([left, left_out])

    startx = 0
    for liste in parts:
        startpoint = [startx+0.1, 0]
        group = DXFList()
        for element in liste:
            startx = max(startx, startpoint[0]+max([x[0] for x in element.data]))
            group.append(dxf.polyline(points=(element.data+startpoint)*1000, layer=element.layer))
        drawing.add(group)
    drawing.save()
    return True

###############CUTS####################
# Check doc/drawings 7-9 for sketches
def cut_1(inner_lists, outer_left, outer_right, amount):
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))
    normvector *= amount

    cuts = []
    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])  # p1,p2,startpoint
    cuts.append(leftcut[0])
    cuts.append(leftcut[0]+normvector)
    for thislist in inner_lists:
        cuts.append(thislist[0][thislist[1]] + normvector)
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])
    cuts.append(rightcut[0]+normvector)
    cuts.append(rightcut[0])

    return cuts, leftcut[1], rightcut[1]


def cut_2(inner_lists, outer_left, outer_right, amount):
    pass






