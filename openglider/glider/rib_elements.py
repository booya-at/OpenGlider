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
#from openglider import Profile2D
from openglider.lines import Node
from openglider.plots.marks import polygon
from openglider.vector import cut, Vectorlist2D


class RigidFoil(object):
    def __init__(self, rib_no, start=-0.1, end=0.1, distance=0.005):
        self.rib_no = rib_no
        self.start = start
        self.end = end
        self.func = lambda x: distance

    def get_3d(self, glider):
        ######NEEDED??
        pass

    def get_length(self, glider):
        flat = self.get_flattened(glider=glider)
        flat = Vectorlist2D(flat)
        flat.check()
        return flat.get_length()

    def get_flattened(self, glider):
        profile = glider.ribs[self.rib_no].profile_2d
        normvectors = Vectorlist2D(profile.normvectors)
        __, start = profile.profilepoint(self.start)
        __, end = profile.profilepoint(self.end)

        list_1 = profile.data.get(start, end)
        list_2 = normvectors.get(start, end)

        return [list_1[i] + self.func(list_1[i]) * list_2[i] for i in range(len(list_1))]


class GibusArcs(object):
    def __init__(self, rib_no, position, size=0.2):
        """A Reinforcement in the form of an arc, in the shape of an arc, to reinforce attachment points"""
        self.rib_no = rib_no
        self.pos = position
        self.size = size
        self.size_abs = False

    def get_3d(self, glider, num_points=10):
        # create circle with center on the point
        gib_arc = self.get_flattened(glider, num_points=num_points)
        rib = glider.ribs[self.rib_no]
        return [rib.align([p[0], p[1], 0]) for p in gib_arc]

    def get_flattened(self, glider, ribs_2d=None, num_points=10):
        # get center point
        profile = glider.ribs[self.rib_no].profile_2d
        start, point_1 = profile.profilepoint(self.pos)
        if self.size_abs:
            point_2 = point_1 + [self.size, 0]
        else:
            __, point_2 = profile.profilepoint(self.pos + self.size)

        gib_arc = [[], []]  # first, second
        circle = polygon(point_1, point_2, num=num_points, is_center=True)[0]
        second = False
        for i in range(len(circle)):
            #print(airfoil.contains_point(circle[i]))
            if profile.contains_point(circle[i]) or \
                    (i < len(circle) - 1 and profile.contains_point(circle[i + 1])) or \
                    (i > 1 and profile.contains_point(circle[i - 1])):
                gib_arc[second].append(circle[i])
            else:
                second = True
        # Cut first and last
        gib_arc = gib_arc[1] + gib_arc[0]  # [secondlist] + [firstlist]
        gib_arc[0], start2, __ = profile.cut(gib_arc[0], gib_arc[1], start)
        gib_arc[-1], stop, __ = profile.cut(gib_arc[-2], gib_arc[-1], start)
        # Append Profile_List
        gib_arc += profile.get(start2, stop).tolist()

        return gib_arc


class AttachmentPoint(Node):
    def __init__(self, number, rib_no, rib_pos, node_type=None):
        super(AttachmentPoint, self).__init__(node_type=2)
        self.rib_no = rib_no
        self.rib_pos = rib_pos
        self.number = number

    def get_position(self, glider):
        rib = glider.ribs[self.rib_no]
        self.vec = rib.profile_3d[rib.profile_2d.profilepoint(self.rib_pos)[0]]
        return self.vec


class RibHole(object):
    def __init__(self, rib_no, pos, size=0.5, numpoints=20):
        self.rib_no = rib_no
        self.pos = pos
        self.size = size
        self.numpoints = numpoints

    def get_3d(self, glider, num=20):
        rib = glider.ribs[self.rib_no]
        hole = self.get_flattened(glider, num=num)
        return [rib.align([p[0], p[1], 0]) for p in hole]

    def get_flattened(self, glider, num=20):
        rib = glider.ribs[self.rib_no]
        p1 = rib.profile_2d.profilepoint(self.pos)[1]
        p2 = rib.profile_2d.profilepoint(-self.pos)[1]
        return polygon(p1, p2, num=num, size=self.size, is_center=False)[0]


class Mylar(object):
    pass

