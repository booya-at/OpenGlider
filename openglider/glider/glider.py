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

import numpy
from openglider.airfoil import Profile2D

from openglider.glider.in_out import IMPORT_GEOMETRY, EXPORT_3D
from openglider.glider.shape import Shape
from openglider.utils import consistent_value
from openglider.plots.projection import flatten_list
from openglider.vector import PolyLine2D
from openglider.vector.functions import norm, rotation_2d


class Glider(object):
    cell_naming_scheme = "c{cell_no}"
    rib_naming_scheme = "r{rib_no}"

    def __init__(self, cells=None, lineset=None):
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
    def __from_json__(cls, cells, ribs, lineset):
        for cell in cells:
            if isinstance(cell.rib1, int):
                cell.rib1 = ribs[cell.rib1]
            if isinstance(cell.rib2, int):
                cell.rib2 = ribs[cell.rib2]
        return cls(cells, lineset=lineset)

    def __repr__(self):
        return """
        {}
        Span: {}
        A/R: {}
        Cells: {}
        """.format(super(Glider, self).__repr__(),
                   self.span,
                   self.aspect_ratio,
                   len(self.cells))

    @classmethod
    def import_geometry(cls, path, filetype=None):
        if not filetype:
            filetype = path.split(".")[-1]
        glider = cls()
        IMPORT_GEOMETRY[filetype](path, glider=glider)
        return glider

    def export_3d(self, path="", *args, **kwargs):
        filetype = path.split(".")[-1]
        return EXPORT_3D[filetype](self, path, *args, **kwargs)

    def rename_parts(self):
        for rib_no, rib in enumerate(self.ribs):
            rib.name = self.rib_naming_scheme.format(rib=rib, rib_no=rib_no)
            rib.rename_parts()

        for cell_no, cell in enumerate(self.cells):
            cell.name = self.cell_naming_scheme.format(cell=cell, cell_no=cell_no)
            cell.rename_parts()

    def return_ribs(self, num=None, ballooning=True):
        """
        Get a list of rib-curves
        :param num: number of midribs per cell
        :param ballooning: calculate ballooned cells
        :return: nested list of ribs [[[x,y,z],p2,p3...],rib2,rib3,..]
        """
        num = num or 0
        num += 1
        if not self.cells:
            return numpy.array([])
        #will hold all the points
        ribs = []
        for cell in self.cells:
            for y in range(num):
                ribs.append(cell.midrib(y * 1. / num, ballooning=ballooning).data)
        ribs.append(self.cells[-1].midrib(1.).data)
        return ribs

    def apply_mean_ribs(self, num_mean=8):
        """
        Calculate Mean ribs
        :param num_mean:
        :return:
        """
        ribs = [cell.mean_rib(num_mean) for cell in self.cells]
        if self.has_center_cell:
            ribs.insert(0, ribs[1])
        else:
            ribs.insert(0, ribs[0])

        for i in range(len(self.ribs))[:-1]:
            self.ribs[i].profile_2d = (ribs[i] + ribs[i+1]) * 0.5

    def return_average_ribs(self, num=0, num_average=8):
        glider = self.copy()
        glider.apply_mean_ribs(num_average)
        return glider.return_ribs(num, ballooning=False)

    @staticmethod
    def return_polygon_indices(ribs):
        num = len(ribs)
        numpoints = len(ribs[0])  # points per rib
        #ribs = numpy.concatenate(ribs)  # ribs was [[point1[x,y,z],[point2[x,y,z]],[point1[x,y,z],point2[x,y,z]]]
        polygons = []
        for i in range(num-1):  # because we use i+1 below
            for k in range(numpoints - 1):  # same reason as above
                kplus = (k+1) % (numpoints-1)
                polygons.append(
                    [i * numpoints + k, i * numpoints + kplus, (i + 1) * numpoints + kplus, (i + 1) * numpoints + k])
        return polygons

    def return_polygons(self, num=None):
        ribs = self.return_ribs(num)
        polygons = self.return_polygon_indices(ribs)
        return polygons, numpy.concatenate(ribs)

    def close_rib(self, rib=-1):
        self.ribs[rib].profile_2d *= 0.

    def get_midrib(self, y=0):
        k = y % 1
        i = int(y - k)
        if i == len(self.cells) and k == 0:  # Stabi-rib
            i -= 1
            k = 1
        return self.cells[i].midrib(k)

    def get_point(self, y=0, x=-1):
        """
        Get a point on the glider
        :param y: span-wise argument (0, cell_no)
        :param x: chord-wise argument (-1, 1)
        :return: point
        """
        rib = self.get_midrib(y)
        rib_no = int(y)
        dy = y - rib_no
        if rib_no == len(self.ribs)-1:
            rib_no -= 1
            dy = 1
        left_rib = self.ribs[rib_no]
        right_rib = self.ribs[rib_no+1]

        ik_l = left_rib.profile_2d(x)
        ik_r = right_rib.profile_2d(x)
        ik = ik_l + dy * (ik_r - ik_l)
        return rib[ik]

    def mirror(self, cutmidrib=True):
        if self.has_center_cell and cutmidrib:  # Cut midrib
            self.cells = self.cells[1:]
        for rib in self.ribs:
            rib.mirror()
        for cell in self.cells:
            cell.mirror(mirror_ribs=False)
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

        # lineset
        for p in other2.lineset.attachment_points:
            p.get_position()
        for node in [node for node in other2.lineset.nodes if node.type==0]:
            node.vec = numpy.array([1, -1, 1]) * node.vec

        other2.lineset.lines += other.lineset.lines
        other2.lineset.sort_lines()

        # rename
        return other2

    def scale(self, faktor):
        for rib in self.ribs:
            rib.pos *= faktor
            rib.chord *= faktor
            # todo: scale lines,

    @property
    def shape_simple(self, cut_center=True):
        """
        Simple (rectangular) shape representation for spline inputs
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

        return Shape(front, back)

    @property
    def shape_flattened(self):
        """
        Projected Shape of the glider (as it would lie on the ground - flattened)
        """
        rot = rotation_2d(numpy.pi / 2)
        front, back = flatten_list(self.get_spanwise(0), self.get_spanwise(1))
        return Shape([rot.dot(p) for p in front], [rot.dot(p) for p in back])

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
        self.set_profile_numpoints(numpoints)

    def set_profile_numpoints(self, numpoints, dist_function=None):
        dist_function = dist_function or Profile2D.cos_2_distribution
        xvalues = dist_function(numpoints)
        for rib in self.ribs:
            rib.profile_2d.x_values = xvalues

    @property
    def profile_x_values(self):
        return self.ribs[0].profile_2d.x_values
        # return consistent_value(self.ribs, 'profile_2d.x_values')

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
    def projected_area(self):
        complete = self.copy_complete()
        return sum(cell.projected_area for cell in complete.cells)

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
            points += self.lineset.get_upper_influence_nodes(line)
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