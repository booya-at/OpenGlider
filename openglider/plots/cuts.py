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
class DesignCut(object):
    def __init__(self, inner_lists, outer_left, outer_right, amount):
        self.inner_lists = inner_lists
        self.outer_left = outer_left
        self.outer_right = outer_right
        self.amount = amount

        self.apply()

    def apply(self):
        p1 = self.inner_lists[0][0][self.inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
        p2 = self.inner_lists[-1][0][self.inner_lists[-1][1]]
        normvector = normalize(rotation_2d(math.pi/2).dot(p1-p2))

        newlist = []
        # todo: sort by distance
        cuts_left = list(self.outer_left.new_cut_2(p1, p2, self.inner_lists[0][1], extrapolate=True))
        cuts_left.sort(key=lambda cut: abs(cut[1]))
        leftcut_index = cuts_left[0][0]
        leftcut = self.outer_left[leftcut_index]

        newlist.append(leftcut)
        newlist.append(leftcut+normvector*self.amount)

        for thislist in self.inner_lists:
            newlist.append(thislist[0][thislist[1]] + normvector*self.amount)

        cuts_right = list(self.outer_right.new_cut_2(p1, p2, self.inner_lists[-1][1], extrapolate=True))
        cuts_right.sort(key=lambda cut: abs(cut[1]))
        rightcut_index = cuts_right[0][0]
        rightcut = self.outer_right[rightcut_index]

        newlist.append(rightcut+normvector*self.amount)
        newlist.append(rightcut)

        self.curve = PolyLine2D(newlist)
        self.index_left = leftcut_index
        self.index_right = rightcut_index

        return self.curve, self.index_left, self.index_right


# OPEN-ENTRY Style
class FoldedCut(DesignCut):
    def __init__(self, inner_lists, outer_left, outer_right, amount, num_folds=2):
        self.num_folds = num_folds
        super(FoldedCut, self).__init__(inner_lists, outer_left, outer_right, amount)

    def apply(self):
        p1 = self.inner_lists[0][0][self.inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
        p2 = self.inner_lists[-1][0][self.inner_lists[-1][1]]
        normvector = normalize(rotation_2d(math.pi/2).dot(p1-p2))

        left_start_index = next(self.outer_left.new_cut(p1, p2, self.inner_lists[0][1], extrapolate=True))
        right_start_index = next(self.outer_right.new_cut(p1, p2, self.inner_lists[-1][1], extrapolate=True))
        left_end_index = next(self.outer_left.new_cut(p1-normvector*self.amount, p2-normvector*self.amount, self.inner_lists[0][1], extrapolate=True))
        right_end_index = next(self.outer_right.new_cut(p1-normvector*self.amount, p2-normvector*self.amount, self.inner_lists[-1][1], extrapolate=True))

        left_start = self.outer_left[left_start_index]
        left_end = self.outer_left[left_end_index]
        right_start = self.outer_right[right_start_index]
        right_end = self.outer_right[right_end_index]

        left_piece = self.outer_left[left_end_index:left_start_index]
        right_piece = self.outer_right[right_end_index:right_start_index]
        left_piece_mirrored = left_piece[::-1]
        right_piece_mirrored = right_piece[::-1]
        left_piece_mirrored.mirror(p1, p2)
        right_piece_mirrored.mirror(p1, p2)

        # mirror to (p1-p2) -> p'=p-2*(p.normvector)
        last_left, last_right = left_start, right_start
        new_left, new_right = PolyLine2D(None), PolyLine2D(None)

        for i in range(self.num_folds):
            left_this = left_piece if i % 2 else left_piece_mirrored
            right_this = right_piece if i % 2 else right_piece_mirrored
            left_this.move(last_left-left_this[0])
            right_this.move(last_right-right_this[0])
            new_left += left_this
            new_right += right_this
            last_left, last_right = new_left.data[-1], new_right.data[-1]


        self.curve = new_left+new_right[::-1]
        self.index_left = left_start_index
        self.index_right = right_start_index

        return self.curve, self.index_left, self.index_right


# TRAILING-EDGE Style
class ParallelCut(DesignCut):
    """
    Cut to continue in a parrallel way (trailing-edge)
    """
    def apply(self):
        p1 = self.inner_lists[0][0][self.inner_lists[0][1]]  # [[list1,pos1],[list2,pos2],...]
        p2 = self.inner_lists[-1][0][self.inner_lists[-1][1]]
        normvector = normalize(rotation_2d(math.pi/2).dot(p1-p2))

        leftcut_index = next(self.outer_left.new_cut(p1, p2, self.inner_lists[0][1], extrapolate=True))
        leftcut = self.outer_left[leftcut_index]
        rightcut_index = next(self.outer_right.new_cut(p1, p2, self.inner_lists[-1][1], extrapolate=True))
        rightcut = self.outer_right[rightcut_index]

        leftcuts_2 = self.outer_left.new_cut(p1-normvector*self.amount, p2-normvector*self.amount, self.inner_lists[0][1], extrapolate=True)
        leftcut_2 = self.outer_left[next(leftcuts_2)]
        rightcuts_2 = self.outer_right.new_cut(p1-normvector*self.amount, p2-normvector*self.amount, self.inner_lists[-1][1], extrapolate=True)
        rightcut_2 = self.outer_right[next(rightcuts_2)]
        diff = (leftcut-leftcut_2 + rightcut - rightcut_2)/2

        newlist = [leftcut, leftcut+diff, rightcut+diff, rightcut]

        self.curve = PolyLine2D(newlist)
        self.index_left = leftcut_index
        self.index_right = rightcut_index

        return newlist, leftcut_index, rightcut_index

cuts = {"orthogonal": DesignCut,
        "folded": FoldedCut,
        "parallel": ParallelCut}