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
from __future__ import division
import math
import copy

import scipy.interpolate
import numpy
from openglider.airfoil import Profile2D

from openglider.glider.in_out import IMPORT_GEOMETRY, EXPORT_3D
from openglider.utils import consistent_value
from openglider.vector import norm, normalize, rotation_2d, mirror2D_x
from openglider.plots.projection import flatten_list
from openglider.utils.bezier import BezierCurve, SymmetricBezier
from openglider.utils import sign


class Glider(object):
    def __init__(self, cells=None, attachment_points=None, lineset=None):
        self.cells = cells or []
        self.lineset = lineset

    def __json__(self):
        new = self.copy()
        ribs = new.ribs[:]
        # de-reference Ribs not to store too much data
        for cell in new.cells:
            cell.rib1 = ribs.index(cell.rib1)
            cell.rib2 = ribs.index(cell.rib2)
        return {"cells": new.cells,
                "ribs": ribs,
                "lineset": self.lineset
                }

    @classmethod
    def import_geometry(cls, path, filetype=None):
        if not filetype:
            filetype = path.split(".")[-1]
        glider = cls()
        IMPORT_GEOMETRY[filetype](path, glider=glider)
        return glider

    def export_geometry(self, path="", filetype=None):
        #if not filetype:
        #    filetype = path.split(".")[-1]
        #EXPORT_GEOMETRY[filetype](self, path)
        pass

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
        numpoints = len(ribs[0])  # points per rib
        ribs = numpy.concatenate(ribs)  # ribs was [[point1[x,y,z],[point2[x,y,z]],[point1[x,y,z],point2[x,y,z]]]
        polygons = []
        for i in range(len(self.cells) * num):  # without +1, because we use i+1 below
            for k in range(numpoints - 1):  # same reason as above
                polygons.append(
                    [i * numpoints + k, i * numpoints + k + 1, (i + 1) * numpoints + k + 1, (i + 1) * numpoints + k])
        return polygons, ribs

    def close_rib(self, rib=-1):
        self.ribs[rib].profile_2d *= 0.

    def get_midrib(self, y=0):
        k = y % 1
        i = int(y - k)
        if i == len(self.cells) and k == 0:  # Stabi-rib
            i -= 1
            k = 1
        return self.cells[i].midrib(k)

    def mirror(self, cutmidrib=True, complete=False):
        # lets assume we have at least one cell to mirror :)
        if self.cells[0].rib1.pos[1] != 0 and cutmidrib:  # Cut midrib
            self.cells = self.cells[1:]
        for rib in self.ribs:
            rib.mirror()
        for cell in self.cells:
            cell.rib1, cell.rib2 = cell.rib2, cell.rib1
        self.cells = self.cells[::-1]

    def copy(self):
        return copy.deepcopy(self)

    def copy_complete(self):
        """Returns a mirrored and combined copy of the glider, ready for export/view"""
        other = self.copy()
        other2 = self.copy()
        other2.mirror()
        other2.cells[-1].rib2 = other.cells[0].rib1
        other2.cells = other2.cells + other.cells
        return other2

    def scale(self, faktor):
        for rib in self.ribs:
            rib.pos *= faktor
            rib.chord *= faktor
            # todo: scale lines,

    @property
    def shape_simple(self):
        """
        Simple shape representation for spline inputs
        """
        last_pos = numpy.array([0, 0])  # y,z
        front = []
        back = []
        x = 0
        for rib in self.ribs:
            width = norm(rib.pos[1:] - last_pos)
            last_pos = rib.pos[1:]

            x += width * (rib.pos[1] > 0)  # x-value
            if x == 0:
                last_pos = numpy.array([0., 0.])
            y_front = -rib.pos[0] + rib.chord * rib.startpos
            y_back = -rib.pos[0] + rib.chord * (rib.startpos - 1)
            front.append([x, y_front])
            back.append([x, y_back])

        return front, back

    @property
    def shape(self):
        """
        Projected Shape of the glider (as it would lie on the ground)
        """
        rot = rotation_2d(numpy.pi / 2)
        front, back = flatten_list(self.get_spanwise(0), self.get_spanwise(1))
        return [rot.dot(p) for p in front], [rot.dot(p) for p in back]

    # delete ? 
    @property
    def arc(self):
        return [rib.pos[1:] for rib in self.ribs]

    @property
    def ribs(self):
        if not self.cells:
            return []
        else:
            ribs = []
            for cell in self.cells:
                for rib in cell.ribs:
                    if rib not in ribs:
                        ribs.append(rib)
            return ribs

    @property
    def profile_numpoints(self):
        return consistent_value(self.ribs, 'profile_2d.numpoints')

    @profile_numpoints.setter
    def profile_numpoints(self, numpoints):
        xvalues = Profile2D.calculate_x_values(numpoints)
        for rib in self.ribs:
            rib.profile_2d.x_values = xvalues

    @property
    def profile_x_values(self):
        return consistent_value(self.ribs, 'profile_2d.x_values')

    @profile_x_values.setter
    def profile_x_values(self, xvalues):
        for rib in self.ribs:
            rib.profile_2d.x_values = xvalues

    @property
    def span(self):
        span = sum([cell.span for cell in self.cells])

        if self.has_center_cell:
            return 2 * span - self.cells[0].span
        else:
            return 2 * span
            # span = 0.
            # front = self.get_spanwise()
            # last = front[0] * [0, 0, 1]  # centerrib only halfed
            # for this in front[1:]:
            #     span += norm((this - last) * [0, 1, 1])
            #     last = this
            #return 2 * span

    @span.setter
    def span(self, span):
        faktor = span / self.span
        self.scale(faktor)

    @property
    def area(self):
        area = 0.
        if len(self.ribs) == 0:
            return 0
        front = self.get_spanwise(0)
        back = self.get_spanwise(1)
        front[0][1] = 0  # Get only half a midrib, if there is...
        back[0][1] = 0
        for i in range(len(front) - 1):
            area += norm(numpy.cross(front[i] - front[i + 1], back[i + 1] - front[i + 1]))
            area += norm(numpy.cross(back[i] - back[i + 1], back[i] - front[i]))
            # By this we get twice the area of half the glider :)
            # http://en.wikipedia.org/wiki/Triangle#Using_vectors
        return area

    @area.setter
    def area(self, area):
        faktor = area / self.area
        self.scale(math.sqrt(faktor))

    @property
    def aspect_ratio(self):
        return self.span ** 2 / self.area

    @aspect_ratio.setter
    def aspect_ratio(self, aspect_ratio):
        area_backup = self.area
        factor = self.aspect_ratio / aspect_ratio
        for rib in self.ribs:
            rib.chord *= factor
        self.area = area_backup

    def get_spanwise(self, x=None):
        """
        Return a list of points for a x_value
        """
        if x is not None:
            return [rib.align([x, 0, 0]) for rib in self.ribs]
        else:
            return [rib.pos for rib in self.ribs]  # This is much faster

    @property
    def attachment_points(self):
        points = []
        for line in self.lineset.lowest_lines:
            points += self.lineset.get_upper_influence_node(line)
        return points

    @property
    def has_center_cell(self):
        return self.ribs[0].pos[1] != 0

    @property
    def glide(self):
        return consistent_value(self.ribs, 'glide')

    @glide.setter
    def glide(self, glide):
        for rib in self.ribs:
            rib.glide = glide
    


class Glider_2D(object):
    """
        a glider 2D object used for gui inputs
    """

    def __init__(self, front=None, back=None, cell_dist=None, arc=None, cell_num=21, parametric=False):
        self.parametric = parametric    #set to False if you change glider 3d manually
        self.cell_num = cell_num  # updates cell pos
        self.front = front or SymmetricBezier()
        self.back = back or SymmetricBezier()
        self.cell_dist = cell_dist or BezierCurve()
        self.arc = arc or BezierCurve()

    def __json__(self):
        return {
            "front": self.front,
            "back": self.back,
            "cell_dist": self.cell_dist
        }

    def arc_pos(self, num=50):
        # calculating the transformed arc
        dist = numpy.array(self.cell_dist_interpolation).T[0] #array of scalars
        arc_arr = [self.arc(0.5)]
        length_arr = [0.]
        for i in numpy.linspace(0.5 + 1 / num, 1, num):
            arc_arr.append(self.arc(i))
            length_arr.append(length_arr[-1] + norm(arc_arr[-2] - arc_arr[-1]))
        int_func = scipy.interpolate.interp1d(length_arr, numpy.array(arc_arr).T)
        normed_dist = [i / dist[-1] * length_arr[-1] for i in dist]
        z_pos = [int_func(i)[1] for i in normed_dist]
        y_pos_temp = [int_func(i)[0] for i in normed_dist]
        y_pos = [0.] if dist[0] == 0 else [y_pos_temp[0]]
        for i, _ in enumerate(z_pos[1:]):
            direction = sign (y_pos_temp[i + 1] - y_pos_temp[i]) #TODO: replace with a better methode
            y_pos.append(y_pos[-1] + direction * numpy.sqrt((normed_dist[i+1] - normed_dist[i]) ** 2 - (z_pos[i + 1] - z_pos[i]) ** 2))
        # return the list of the arc positions and a scale factor to transform back to the real span
        return numpy.array(zip(y_pos, z_pos)).tolist()


    def arc_pos_angle(self, num=50):
        arc_pos = self.arc_pos(num=num)
        arc_pos_copy = copy.copy(arc_pos)
        dist = numpy.array(self.cell_dist_interpolation).T[0]
        # calculating the rotation of the ribs
        if arc_pos[0][0] == 0.:
            arc_pos = [[-arc_pos[1][0], arc_pos[1][1]]] + arc_pos
        else:
            arc_pos = [[0., arc_pos[0][1]]] + arc_pos
        arc_pos = numpy.array(arc_pos)
        arc_angle = []
        rot = rotation_2d(-numpy.pi / 2)
        for i, pos in enumerate(arc_pos[1:-1]):
            direction = rot.dot(normalize(pos - arc_pos[i])) + rot.dot(normalize(arc_pos[i + 2] - pos))
            arc_angle.append(numpy.arctan2(*direction))
        temp = arc_pos[-1] - arc_pos[-2]
        arc_angle.append(- numpy.arctan2(temp[1], temp[0]))

        # transforming the start_pos back to the original distribution
        arc_pos = numpy.array(arc_pos_copy)
        if arc_pos_copy[0][0] != 0.:
            arc_pos_copy = [[0., arc_pos_copy[0][1]]] + arc_pos_copy
        arc_pos_copy = numpy.array(arc_pos_copy)
        arc_normed_length = 0.
        # recalc actuall length
        for i, pos in enumerate(arc_pos_copy[1:]):
            arc_normed_length += norm(arc_pos_copy[i] - pos)
        trans = - numpy.array(arc_pos_copy[0])
        scal = dist[-1] / arc_normed_length
        # first translate the middle point to [0, 0]
        arc_pos += trans
        #scale to the original distribution
        arc_pos *= scal
        arc_pos = arc_pos.tolist()

        return arc_pos, arc_angle

    def shape(self, num=30):
        """ribs, front, back"""
        return self.interactive_shape(num)[:-1]

    def interactive_shape(self, num=30):
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        dist_line = self.cell_dist_interpolation
        dist = [i[0] for i in dist_line]
        front = map(front_int, dist)
        front = mirror2D_x(front)[::-1] + front
        back = map(back_int, dist)
        back = mirror2D_x(back)[::-1] + back
        ribs = zip(front, back)
        return [ribs, front, back, dist_line]

    @property
    def cell_dist_controlpoints(self):
        return self.cell_dist.controlpoints[1:-1]

    @cell_dist_controlpoints.setter
    def cell_dist_controlpoints(self, arr):
        self.cell_dist.controlpoints = [[0, 0]] + arr + [[self.front.controlpoints[-1][0], 1]]

    @property
    def cell_dist_interpolation(self):
        interpolation = self.cell_dist.interpolate_3d(num=20, which=1)
        start = (self.cell_num % 2) / self.cell_num
        return [interpolation(i) for i in numpy.linspace(start, 1, num=self.cell_num // 2 + 1)]

    def depth_integrated(self, num=100):
        l = numpy.linspace(0, self.front.controlpoints[-1][0], num)
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        integrated_depth = [0.]
        for i in l[1:]:
            integrated_depth.append(integrated_depth[-1] + 1. / (front_int(i)[1] - back_int(i)[1]))
        return zip(l, [i / integrated_depth[-1] for i in integrated_depth])

    @classmethod
    def fit_glider(cls, glider, numpoints=3):
        # todo: create glider2d from glider obj (fit bezier)
        def mirror_x(polyline):
            mirrored = [[-p[0], p[1]] for p in polyline[1:]]
            start = polyline[0][0] < 0
            return mirrored[::-1] + polyline[start:]

        front, back = glider.shape_simple
        arc = [rib.pos[1:] for rib in glider.ribs]
        front_bezier = SymmetricBezier.fit(mirror_x(front), numpoints=numpoints)
        back_bezier = SymmetricBezier.fit(mirror_x(back), numpoints=numpoints)
        arc_bezier = SymmetricBezier.fit(mirror_x(arc), numpoints=numpoints)


        cell_num = len(glider.cells) * 2
        if glider.ribs[0].pos[1] < 0:
            cell_num -= 1
        front[0][0] = 0  # for midribs
        start = (2 - (cell_num % 2)) / cell_num
        const_arr = [0.] + numpy.linspace(start, 1, len(front) - 1).tolist()
        rib_pos = [0.] + [p[0] for p in front[1:]]
        print(zip(rib_pos, const_arr))
        rib_distribution = BezierCurve.fit(zip(rib_pos, const_arr), numpoints=numpoints + 3)
        gl2d = cls(front=front_bezier,
                   back=back_bezier,
                   cell_dist=rib_distribution,
                   cell_num=cell_num,
                   arc=arc_bezier,
                   parametric=True)
        return gl2d

    def glider_3d(self, glider, num=50):
        """returns a new glider from parametric values"""
        ribs = []
        cells = []


        # TODO airfoil, ballooning, arc-------
        from openglider.airfoil import Profile2D
        airfoil = glider.ribs[0].profile_2d
        glide = 8.
        aoa = numpy.deg2rad(13.)
        #--------------------------------------

        from openglider.glider import Rib, Cell
        dist = [i[0] for i in self.cell_dist_interpolation]
        front_int = self.front.interpolate_3d(num=num)
        back_int = self.back.interpolate_3d(num=num)
        arc_pos, arc_angle = self.arc_pos_angle(num=num)
        if dist[0] != 0.:
            # adding the mid cell
            dist = [-dist[0]] + dist
            arc_pos = [[-arc_pos[0][0], arc_pos[0][1]]] + arc_pos
            arc_angle = [-arc_angle[0]] + arc_angle

        for i, pos in enumerate(dist):
            fr = front_int(pos)
            ba = back_int(pos)
            ar = arc_pos[i]
            ribs.append(Rib(
                profile_2d=airfoil,
                startpoint= numpy.array([-fr[1], ar[0], ar[1]]),
                chord=norm(fr - ba),
                arcang = arc_angle[i],
                glide=glide,
                aoa = aoa
                ))
        for i, rib in enumerate(ribs[1:]):
            cells.append(Cell(ribs[i], rib, []))
            glider.cells = cells

if __name__ == "__main__":
    from openglider.jsonify import dump, loads
    a = Glider.import_geometry("../../tests/demokite.ods")
    b = Glider_2D.fit_glider(a)
    b.interactive_shape()


