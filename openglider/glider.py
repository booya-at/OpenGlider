__author__ = 'simon'
import numpy
import copy

from openglider.Import import ODFImport2
from . import Graphics as Graph

#holds the importfunctions
IMPORT_NAMES = {
    'ods': ODFImport2.import_ods,
}


class Glider(object):
    def __init__(self):
        self.cells = []

    def import_from_file(self, path, filetype='ods'):
        IMPORT_NAMES[filetype](path, self)

    def output_polygons(self, num):
        #will hold all the points
        ribs = []
        for cell in self.cells:
            for y in range(num):
                ribs.append(cell.midrib(y*1./num).data)
        ribs.append(self.cells[-1].midrib(1.).data)
        # ribs is [[point1[x,y,z],[point2[x,y,z]],[point1[x,y,z],point2[x,y,z]]]

        # num*cells+1 ribs

        points = len(ribs[0])
        ribs = numpy.concatenate(ribs)
        polygons = []

        for i in range(len(self.cells)*num):  # without +1, because we us i+1 below
            for k in range(points-1):  # same reason as above
                polygons.append(Graph.Polygon([i*points+k, i*points+k+1, (i+1)*points+k+1, (i+1)*points+k]))

        Graph.Graphics3D(polygons, ribs)

    def get_midrib(self, y=0):
        k = y % 1
        i = y - k
        if i == len(self.cells) and k == 0:
            i -= 1
            k = 1
        return self.cells[i].midrib(k)

    def _get_ribs_(self):
        if not self.cells:
            return []
        return [self.cells[0].rib1] + [cell.rib2 for cell in self.cells]

    def recalc(self):
        for cell in self.cells:
            cell.recalc()

    def mirror(self, cut=True):
        #cell1 = self.cells[0]
        if not self.cells:
            return
        if self.cells[0].rib1.pos[1] != 0 and cut:
            self.cells = self.cells[1:]
        for rib in self.ribs:
            rib.mirror()

    def copy(self):
        return copy.deepcopy(self)

    ribs = property(fget=_get_ribs_)






