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


__author__ = 'simon'
import numpy
import copy

from openglider.Import import ODFImport
from . import Graphics as Graph

#holds the importfunctions
IMPORT_EXPORT_NAMES = {
    'ods': [ODFImport.import_ods, lambda x, y: y],
}


class Glider(object):
    def __init__(self):
        self.cells = []

    def import_from_file(self, path, filetype='ods'):
        IMPORT_EXPORT_NAMES[filetype][0](path, self)

    def return_polygons(self, num):
        if not self.cells:
            return numpy.array([]), numpy.array([])
        #will hold all the points
        ribs = []
        for cell in self.cells:
            for y in range(num):
                ribs.append(cell.midrib_basic_cell(y*1./num).data)
        ribs.append(self.cells[-1].midrib_basic_cell(1.).data)

        #points per rib
        points = len(ribs[0])
        # ribs is [[point1[x,y,z],[point2[x,y,z]],[point1[x,y,z],point2[x,y,z]]]
        ribs = numpy.concatenate(ribs)
        #now ribs is flat
        polygons = []

        for i in range(len(self.cells)*num):  # without +1, because we us i+1 below
            for k in range(points-1):  # same reason as above
                polygons.append([i*points+k, i*points+k+1, (i+1)*points+k+1, (i+1)*points+k])
        return polygons, ribs

    def close_rib(self, rib=-1):
        self.ribs[rib].profile_2d *= 0.01
        self.ribs[rib].recalc()

    def get_midrib(self, y=0):
        k = y % 1
        i = y - k
        if i == len(self.cells) and k == 0:  # Stabi-rib
            i -= 1
            k = 1
        return self.cells[i].midrib_basic_cell(k)

    def _get_ribs_(self):
        if not self.cells:
            return []
        return [self.cells[0].rib1] + [cell.rib2 for cell in self.cells]

    def mirror(self, cutmidrib=True):
        if not self.cells:
            return
        if self.cells[0].rib1.pos[1] != 0 and cutmidrib:  # Cut midrib
            self.cells = self.cells[1:]
        for rib in self.ribs:
            rib.mirror()
        for cell in self.cells:
            first = cell.rib1
            cell.rib1 = cell.rib2
            cell.rib2 = first

    def recalc(self):
        for rib in self.ribs:
            rib.recalc()
        for cell in self.cells:
            cell.recalc()

    def copy(self):
        return copy.deepcopy(self)

    def export(self, path, file_type='ods'):
        IMPORT_EXPORT_NAMES[file_type][1](self, path)

    ribs = property(fget=_get_ribs_)






