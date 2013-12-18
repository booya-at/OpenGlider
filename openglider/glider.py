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
from openglider.Vector import normalize
from openglider.Import import obj
from . import Graphics as Graph

#holds the importfunctions TODO: Just import the whole array
IMPORT_NAMES = {
    'ods': ODFImport.import_ods,
    'obj': []
}
EXPORT_NAMES = {
    'ods': lambda x, y: x

}


class Glider(object):
    def __init__(self):
        self.cells = []

    def import_from_file(self, path, filetype='ods'):
        IMPORT_NAMES[filetype](path, self)

    def export_to_file(self, path="", filetype=None):
        if not filetype:
            filetype = path.split(".")[-1]
        EXPORT_NAMES[filetype](path, self)


        # array = other.cells[::-1] + self.cells
    def return_ribs(self, num=0):
        if not self.cells:
            return numpy.array([])
        num += 1
        #will hold all the points
        ribs = []
        for cell in self.cells:
            for y in range(num):
                ribs.append(cell.midrib(y * 1. / num).data)
        ribs.append(self.cells[-1].midrib(1.).data)
        return ribs

    def export_obj(self, path, midribs=0, numpoints=None, floatnum=6):
        if numpoints:
            pass
        other = self.copy()
        other.mirror()
        other.cells[0].rib2 = self.cells[0].rib1
        other.cells = other.cells[::-1] + self.cells
        other.recalc()
        ribs = other.return_ribs(midribs)
        normvectors = []
        panels = []
        points = []
        numpoints = len(ribs[0])
        for i in range(len(ribs)):
            for j in range(numpoints):
                # Create two Triangles from one rectangle:
                # rectangle: [i * numpoints + k, i * numpoints + k + 1, (i + 1) * numpoints + k + 1, (i + 1) * numpoints + k])
                # Start counting from 1!!
                panels.append([i*numpoints + j+1, i*numpoints + j+2, (i+1)*numpoints + j+2])
                panels.append([(i+1)*numpoints + j+1, i*numpoints + j+1, (i+1)*numpoints + j+2])
                # Calculate normvectors
                first = ribs[i+(i < len(ribs)-1)][j] - ribs[i-(i > 0)][j]  # Y-Axis
                second = ribs[i][j-(j > 0)]-ribs[i][j+(j < numpoints-1)]
                points.append((ribs[i][j], normalize(numpy.cross(first, second))))
        panels = panels[:2*(len(ribs)-1)*(numpoints)-2]
        # Write file
        outfile = open(path, "w")
        for point in points:
            point = point[0]*[-1,-1,-1], point[1]*[-1,-1,-1]
            outfile.write("vn")
            for coord in point[1]:
                outfile.write(" "+str(round(coord, floatnum)))
            outfile.write("\n")
            outfile.write("v")
            for coord in point[0]:
                outfile.write(" "+str(round(coord, floatnum)))
            outfile.write("\n")
        #outfile.write("# "+str(len(points))+" vertices, 0 vertices normals\n\n")
        for polygon in panels:
            outfile.write("f")
            for point in polygon:
                outfile.write(" "+str(point)+"//"+str(point))
            outfile.write("\n")
        #outfile.write("# "+str(len(panels))+" faces, 0 coords texture\n\n# End of File")
        print(len(points),len(normvectors),len(panels),max(panels,key=lambda x: max(x)))

        outfile.close()


    def return_polygons(self, num=0):
        if not self.cells:
            return numpy.array([]), numpy.array([])
        ribs = self.return_ribs(num)
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


    ribs = property(fget=_get_ribs_)






