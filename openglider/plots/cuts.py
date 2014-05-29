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
import openglider.vector


###############CUTS####################
# Check doc/drawings 7-9 for sketches
# DESIGN-CUT Style
def cut_1(inner_lists, outer_left, outer_right, amount):
    """
    Orthogonal Cut for design-cuts
    """
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.vector.normalize(openglider.vector.rotation_2d(math.pi/2).dot(p1-p2))

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


# OPEN-ENTRY Style
def cut_2(inner_lists, outer_left, outer_right, amount, num_folds=2):
    """
    Cut to fold material (open-entry, diagonals,..)
    """
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.vector.normalize(openglider.vector.rotation_2d(math.pi/2).dot(p1-p2))

    left_start = outer_left.cut(p1, p2, inner_lists[0][1])
    right_start = outer_right.cut(p1, p2, inner_lists[-1][1])
    left_end = outer_left.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1])
    right_end = outer_right.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1])

    left_piece = outer_left[left_end[1]:left_start[1]]
    right_piece = outer_right[right_end[1]:right_start[1]]
    left_piece_mirrored = left_piece[::-1]
    right_piece_mirrored = right_piece[::-1]
    left_piece_mirrored.mirror(p1, p2)
    right_piece_mirrored.mirror(p1, p2)

    # mirror to (p1-p2) -> p'=p-2*(p.normvector)
    last_left, last_right = left_start[0], right_start[0]
    new_left, new_right = openglider.Vectorlist2D(), openglider.Vectorlist2D()

    for i in range(num_folds):
        left_this = left_piece if i%2 else left_piece_mirrored
        right_this = right_piece if i%2 else right_piece_mirrored
        left_this.shift(last_left-left_this[0])
        right_this.shift(last_right-right_this[0])
        new_left += left_this
        new_right += right_this
        last_left, last_right = new_left.data[-1], new_right.data[-1]

    return new_left+new_right[::-1], left_start[1], right_start[1]


# TRAILING-EDGE Style
def cut_3(inner_lists, outer_left, outer_right, amount):
    """
    Cut to continue in a parrallel way (trailing-edge)
    """
    # Continue Parallel
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = openglider.vector.normalize(openglider.vector.rotation_2d(math.pi/2).dot(p1-p2))

    leftcut = outer_left.cut(p1, p2, inner_lists[0][1])
    rightcut = outer_right.cut(p1, p2, inner_lists[-1][1])

    leftcut_2 = outer_left.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1])
    rightcut_2 = outer_right.cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1])
    diff = (leftcut[0]-leftcut_2[0] + rightcut[0] - rightcut_2[0])/2

    newlist = [leftcut[0], leftcut[0]+diff, rightcut[0]+diff, rightcut[0]]

    return newlist, leftcut[1], rightcut[1]

cuts = [cut_1, cut_2, cut_3]