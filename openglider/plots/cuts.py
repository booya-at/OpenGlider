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

from openglider.vector.functions import normalize, rotation_2d
from openglider.vector.polyline import PolyLine2D

###############CUTS####################
# Check doc/drawings 7-9 for sketches
# DESIGN-CUT Style
def cut_1(inner_lists, outer_left, outer_right, amount):
    """
    Orthogonal Cut for design-cuts
    """
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = normalize(rotation_2d(math.pi/2).dot(p1-p2))

    newlist = []
    leftcut_index = next(outer_left.new_cut(p1, p2, inner_lists[0][1], extrapolate=True))  # p1,p2,startpoint
    leftcut = outer_left[leftcut_index]
    newlist.append(leftcut)
    newlist.append(leftcut+normvector*amount)
    for thislist in inner_lists:
        newlist.append(thislist[0][thislist[1]] + normvector*amount)
    rightcut_index = next(outer_right.new_cut(p1, p2, inner_lists[-1][1], extrapolate=True))
    rightcut = outer_right[rightcut_index]
    newlist.append(rightcut+normvector*amount)
    newlist.append(rightcut)

    return newlist, leftcut_index, rightcut_index


# OPEN-ENTRY Style
def cut_2(inner_lists, outer_left, outer_right, amount, num_folds=2):
    """
    Cut to fold material (open-entry, diagonals,..)
    """
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = normalize(rotation_2d(math.pi/2).dot(p1-p2))

    left_start_index = next(outer_left.new_cut(p1, p2, inner_lists[0][1], extrapolate=True))
    right_start_index = next(outer_right.new_cut(p1, p2, inner_lists[-1][1], extrapolate=True))
    left_end_index = next(outer_left.new_cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1], extrapolate=True))
    right_end_index = next(outer_right.new_cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1], extrapolate=True))

    left_start = outer_left[left_start_index]
    left_end = outer_left[left_end_index]
    right_start = outer_right[right_start_index]
    right_end = outer_right[right_end_index]

    left_piece = outer_left[left_end_index:left_start_index]
    right_piece = outer_right[right_end_index:right_start_index]
    left_piece_mirrored = left_piece[::-1]
    right_piece_mirrored = right_piece[::-1]
    left_piece_mirrored.mirror(p1, p2)
    right_piece_mirrored.mirror(p1, p2)

    # mirror to (p1-p2) -> p'=p-2*(p.normvector)
    last_left, last_right = left_start, right_start
    new_left, new_right = PolyLine2D(None), PolyLine2D(None)

    for i in range(num_folds):
        left_this = left_piece if i % 2 else left_piece_mirrored
        right_this = right_piece if i % 2 else right_piece_mirrored
        left_this.move(last_left-left_this[0])
        right_this.move(last_right-right_this[0])
        new_left += left_this
        new_right += right_this
        last_left, last_right = new_left.data[-1], new_right.data[-1]

    return new_left+new_right[::-1], left_start_index, right_start_index


# TRAILING-EDGE Style
def cut_3(inner_lists, outer_left, outer_right, amount):
    """
    Cut to continue in a parrallel way (trailing-edge)
    """
    # Continue Parallel
    p1 = inner_lists[0][0][inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
    p2 = inner_lists[-1][0][inner_lists[-1][1]]
    normvector = normalize(rotation_2d(math.pi/2).dot(p1-p2))

    leftcut_index = next(outer_left.new_cut(p1, p2, inner_lists[0][1], extrapolate=True))
    leftcut = outer_left[leftcut_index]
    rightcut_index = next(outer_right.new_cut(p1, p2, inner_lists[-1][1], extrapolate=True))
    rightcut = outer_right[rightcut_index]

    leftcuts_2 = outer_left.new_cut(p1-normvector*amount, p2-normvector*amount, inner_lists[0][1], extrapolate=True)
    leftcut_2 = outer_left[next(leftcuts_2)]
    rightcuts_2 = outer_right.new_cut(p1-normvector*amount, p2-normvector*amount, inner_lists[-1][1], extrapolate=True)
    rightcut_2 = outer_right[next(rightcuts_2)]
    diff = (leftcut-leftcut_2 + rightcut - rightcut_2)/2

    newlist = [leftcut, leftcut+diff, rightcut+diff, rightcut]

    return newlist, leftcut_index, rightcut_index

cuts = {"orthogonal": cut_1,
        "folded": cut_2,
        "parallel": cut_3}