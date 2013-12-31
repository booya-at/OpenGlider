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
import numpy
import copy

from openglider.Import import IMPORT_GEOMETRY, EXPORT_3D
from openglider.Vector import norm, normalize


class Glider(object):
    def __init__(self):
        self.cells = []
        self.data = {}

    def import_geometry(self, path, filetype=None):
        if not filetype:
            filetype = path.split(".")[-1]
        IMPORT_GEOMETRY[filetype](path, self)

    def export_geometry(self, path="", filetype=None):
        if not filetype:
            filetype = path.split(".")[-1]
            #EXPORT_NAMES[filetype](self, path)

    def export_3d(self, path="", filetype=None, midribs=0, numpoints=None, floatnum=6):
        if not filetype:
            filetype = path.split(".")[-1]
        EXPORT_3D[filetype](self, path, midribs, numpoints, floatnum)

    def return_ribs(self, num=0):
        if not self.cells:
            return numpy.array([])
        num += 1
        #will hold all the points
        ribs = []
        #print(len(self.cells))
        for cell in self.cells:
            for y in range(num):
                ribs.append(cell.midrib(y * 1. / num).data)
        ribs.append(self.cells[-1].midrib(1.).data)
        return ribs

    def return_polygons(self, num=0):
        if not self.cells:
            return numpy.array([]), numpy.array([])
        ribs = self.return_ribs(num)
        num += 1
        #points per rib
        numpoints = len(ribs[0])
        # ribs is [[point1[x,y,z],[point2[x,y,z]],[point1[x,y,z],point2[x,y,z]]]
        ribs = numpy.concatenate(ribs)
        #now ribs is flat
        polygons = []
        for i in range(len(self.cells) * num):  # without +1, because we use i+1 below
            for k in range(numpoints - 1):  # same reason as above
                polygons.append(
                    [i * numpoints + k, i * numpoints + k + 1, (i + 1) * numpoints + k + 1, (i + 1) * numpoints + k])
        return polygons, ribs

    def close_rib(self, rib=-1):
        self.ribs[rib].profile_2d *= 0.
        self.ribs[rib].recalc()

    def get_midrib(self, y=0):
        k = y % 1
        i = y - k
        if i == len(self.cells) and k == 0:  # Stabi-rib
            i -= 1
            k = 1
        return self.cells[i].midrib_basic_cell(k)

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
        self.cells = self.cells[::-1]

    def recalc(self):
        for rib in self.ribs:
            rib.recalc()
        for cell in self.cells:
            cell.recalc()

    def copy(self):
        return copy.deepcopy(self)

    def scale(self, faktor):
        for rib in self.ribs:
            rib.pos *= faktor
            rib.chord *= faktor

    def __get_ribs_(self):
        if not self.cells:
            return []
        return [self.cells[0].rib1] + [cell.rib2 for cell in self.cells]

    def __get_numpoints(self):
        return self.ribs[0].profile_2d.numpoints

    def __set_numpoints(self, numpoints):
        self.ribs[0].profile_2d.numpoints = numpoints
        xvalues = self.ribs[0].profile_2d.XValues
        for rib in self.ribs:
            rib.profile_2d.x_values = xvalues

    def __get_span(self):
        span = 0.
        last = numpy.array([0, 0, 0])
        for rib in self.ribs[1:]:
            span += norm((rib.pos - last) * [0, 1, 1])
            last = rib.pos
        return 2 * span

    def __set_span(self, span):
        faktor = span / self.span
        self.scale(faktor)

    def __get_area(self):
        area = 0.
        if len(self.ribs) == 0:
            return 0
        lastrib_front = self.ribs[0].align([0, 0, 0]) * numpy.array([1, 0, 1])
        lastrib_back = self.ribs[0].align([1, 0, 0]) * numpy.array([1, 0, 1])
        for rib in self.ribs[1:]:
            thisrib_front = rib.align([0, 0, 0]) * numpy.array([1, 0, 1])
            thisrib_back = rib.align([1, 0, 0]) * numpy.array([1, 0, 1])
            area += norm(numpy.cross(lastrib_front - thisrib_front, thisrib_back - thisrib_front))
            area += norm(numpy.cross(lastrib_back - thisrib_back, thisrib_back - thisrib_front))
            lastrib_back = thisrib_back
            lastrib_front = thisrib_front
        return area

    def __set_area(self, area):
        faktor = area / self.area
        self.scale(math.sqrt(faktor))

    ribs = property(fget=__get_ribs_)
    numpoints = property(__get_numpoints, __set_numpoints)
    span = property(__get_span, __set_span)
    area = property(__get_area, __set_area)






