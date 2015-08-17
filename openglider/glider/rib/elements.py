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
import numpy
from openglider.lines import Node
from openglider.plots.marks import polygon
from openglider.vector.functions import cut
from openglider.vector.polyline import PolyLine2D


class RigidFoil(object):
    def __init__(self, start=-0.1, end=0.1, distance=0.005):
        self.start = start
        self.end = end
        self.distance = distance
        self.func = lambda x: distance

    def __json__(self):
        return {'start': self.start,
                'end': self.end,
                'distance': self.distance}

    def get_3d(self, rib):
        return [rib.align(p, scale=False) for p in self.get_flattened(rib)]

    def get_length(self, rib):
        return self.get_flattened(rib).get_length()

    def get_flattened(self, rib):
        flat = PolyLine2D(self._get_flattened(rib))
        flat.check()
        return flat

    def _get_flattened(self, rib):
        profile = rib.profile_2d
        profile_normvectors = PolyLine2D(profile.normvectors)
        start = profile(self.start)
        end = profile(self.end)

        outer_curve = profile[start:end].scale(rib.chord)
        normvectors = profile_normvectors[start:end]

        return [p - n*self.func(p) for p, n in zip(outer_curve, normvectors)]


class GibusArcs(object):
    """
    A Reinforcement, in the shape of an arc, to reinforce attachment points
    """
    def __init__(self, position, size=0.2, material_code=None):
        self.pos = position
        self.size = size
        self.size_abs = False
        self.material_code = material_code or ""

    def __json__(self):
        return {'position': self.pos,
                'size': self.size}

    def get_3d(self, rib, num_points=10):
        # create circle with center on the point
        gib_arc = self.get_flattened(rib, num_points=num_points)
        return [rib.align([p[0], p[1], 0], scale=False) for p in gib_arc]

    def get_flattened(self, rib, num_points=10):
        # get center point
        profile = rib.profile_2d
        start = profile(self.pos)
        point_1 = profile[start]

        if self.size_abs:
            # reverse scale now
            size = self.size / rib.chord
        else:
            size = self.size
        point_2 = profile.profilepoint(self.pos + size)

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

        return numpy.array(gib_arc) * rib.chord


# Node from lines
class AttachmentPoint(Node):
    def __init__(self, rib, name, rib_pos, force=None):
        super(AttachmentPoint, self).__init__(node_type=2)
        self.rib = rib
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

    def __json__(self):
        return {"rib": self.rib,
                "number": self.name,
                "rib_pos": self.rib_pos,
                "force": self.force}

    def get_position(self):
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec


class RibHole(object):
    def __init__(self, pos, size=0.5):
        self.pos = pos
        self.size = size

    def get_3d(self, rib, num=20):
        hole = self.get_flattened(rib, num=num)
        return [rib.align([p[0], p[1], 0]) for p in hole]

    def get_flattened(self, rib, num=20):
        prof = rib.profile_2d
        p1 = prof[prof(self.pos)]
        p2 = prof[prof(-self.pos)]

        return polygon(p1, p2, num=num, scale=self.size, is_center=False)[0]


class Mylar(object):
    pass

