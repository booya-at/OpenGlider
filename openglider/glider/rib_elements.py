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
from openglider.vector.functions import cut
from openglider.vector.polyline import PolyLine2D


class RigidFoil(object):
    def __init__(self, rib, start=-0.1, end=0.1, distance=0.005):
        self.rib = rib
        self.start = start
        self.end = end
        self.distance = distance
        self.func = lambda x: distance

    def __json__(self):
        return {'rib': self.rib,
                'start': self.start,
                'end': self.end,
                'distance': self.distance}

    def get_3d(self, glider):
        ######NEEDED??
        pass

    def get_length(self):
        flat = self.get_flattened()
        flat = PolyLine2D(flat)
        flat.check()
        return flat.get_length()

    def get_flattened(self):
        profile = self.rib.profile_2d
        normvectors = PolyLine2D(profile.normvectors)
        __, start = profile.profilepoint(self.start)
        __, end = profile.profilepoint(self.end)

        list_1 = profile.data.get(start, end)
        list_2 = normvectors.get(start, end)

        return [list_1[i] + self.func(list_1[i]) * list_2[i] for i in range(len(list_1))]


class GibusArcs(object):
    """
    A Reinforcement, in the shape of an arc, to reinforce attachment points
    """
    def __init__(self, rib, position, size=0.2):
        self.rib = rib
        self.pos = position
        self.size = size
        self.size_abs = False

    def __json__(self):
        return {'rib': self.rib,
                'position': self.pos,
                'size': self.size}

    def get_3d(self, num_points=10):
        # create circle with center on the point
        gib_arc = self.get_flattened(num_points=num_points)
        return [self.rib.align([p[0], p[1], 0]) for p in gib_arc]

    def get_flattened(self, ribs_2d=None, num_points=10):
        # get center point
        profile = self.rib.profile_2d
        start = profile(self.pos)
        point_1 = profile[start]
        if self.size_abs:
            point_2 = point_1 + [self.size, 0]
        else:
            point_2 = profile.profilepoint(self.pos + self.size)

        gib_arc = [[], []]  # first, second
        circle = polygon(point_1, point_2, num=num_points, is_center=True)[0][1:]
        is_second_run = False
        #print(circle)
        for i in range(len(circle)):
            #print(airfoil.contains_point(circle[i]))
            if profile.contains_point(circle[i]) or \
                    (i < len(circle) - 1 and profile.contains_point(circle[i + 1])) or \
                    (i > 1 and profile.contains_point(circle[i - 1])):
                gib_arc[is_second_run].append(circle[i])
            else:
                is_second_run = True
        # Cut first and last
        gib_arc = gib_arc[1] + gib_arc[0]  # [secondlist] + [firstlist]
        start2 = profile.new_cut(gib_arc[0], gib_arc[1], start)
        #print(gib_arc)
        stop = profile.new_cut(gib_arc[-2], gib_arc[-1], start)
        # Append Profile_List
        gib_arc += profile.get(start2.next(), stop.next()).tolist()

        return gib_arc


# Node from lines
class AttachmentPoint(Node):
    def __init__(self, rib, number, rib_pos, force=None):
        super(AttachmentPoint, self).__init__(node_type=2)
        self.rib = rib
        self.rib_pos = rib_pos
        self.number = number
        self.force = force

    def __json__(self):
        return {"rib": self.rib,
                "number": self.number,
                "rib_pos": self.rib_pos,
                "force": self.force}

    def get_position(self):
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec


class RibHole(object):
    def __init__(self, rib, pos, size=0.5, numpoints=20):
        self.rib = rib
        self.pos = pos
        self.size = size
        self.numpoints = numpoints

    def get_3d(self, num=20):
        hole = self.get_flattened(num=num)
        print("aha", [p for p in hole])
        return [self.rib.align([p[0], p[1], 0]) for p in hole]

    def get_flattened(self, num=20):
        p1 = self.rib.profile_2d.profilepoint(self.pos)
        p2 = self.rib.profile_2d.profilepoint(-self.pos)
        return polygon(p1, p2, num=num, scale=self.size, is_center=False)[0]


class Mylar(object):
    pass

