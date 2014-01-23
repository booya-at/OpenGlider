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
# DESIGN-CUT Style
def cut_1(inner_lists, outer_left, outer_right, amount):
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))

    newlist = []
    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])  # p1,p2,startpoint
    newlist.append(leftcut[0])
    newlist.append(leftcut[0]+normvector*amount)
    for thislist in inner_lists:
        newlist.append(thislist[0][thislist[1]] + normvector*amount)
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])
    newlist.append(rightcut[0]+normvector*amount)
    newlist.append(rightcut[0])

    return newlist, leftcut[1], rightcut[1]


# OPEN-ENTRY-STYLE
def cut_2(inner_lists, outer_left, outer_right, amount):
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))

    newlist = []
    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])

    leftcut_2 = outer_left.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1])
    rightcut_2 = outer_right.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1])

    piece1 = outer_left[leftcut[1]:leftcut_2[1]]
    piece2 = outer_right[rightcut[1]:rightcut_2[1]]

    # mirror to (p1-p2) -> p'=p-2*(p.normvector)

    for point in piece1[::]:
        newlist.append(point - 2*normvector*normvector.dot(point-leftcut[0]))
    last = newlist[-1]
    for point in piece1[::-1]:
        newlist.append(-(leftcut_2[0] - point) + last)

    cuts2 = []
    for point in piece2[::]:
        cuts2.append(point - 2*normvector*normvector.dot(point-rightcut[0]))
    last = cuts2[-1]
    for point in piece2[::-1]:
        cuts2.append(-(rightcut_2[0] - point) + last)

    return newlist+cuts2[::-1], leftcut[1], rightcut[1]


def cut_3(inner_lists, outer_left, outer_right, amount):
    ## Continue Parallel
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.Vector.normalize(openglider.Vector.rotation_2d(math.pi/2).dot(p1-p2))

    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])

    leftcut_2 = outer_left.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1])
    rightcut_2 = outer_right.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1])
    diff = (leftcut[0]-leftcut_2[0] + rightcut[0] - rightcut_2[0])/2

    newlist = [leftcut[0], leftcut[0]+diff, rightcut[0]+diff, rightcut[0]]

    return newlist, leftcut[1], rightcut[1]

cuts = [cut_1, cut_2, cut_3]






