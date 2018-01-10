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
import numpy as np
import math

from openglider.lines import Node
from openglider.plots.marks import Polygon
from openglider.vector.polyline import PolyLine2D
from openglider.vector.functions import set_dimension
from openglider.vector.spline import Bezier
from openglider.vector import norm
from openglider.vector.transformation import Rotation, Translation


class RigidFoil(object):
    def __init__(self, start=-0.1, end=0.1, distance=0.005, circle_radius=0.03):
        self.start = start
        self.end = end
        self.distance = distance
        self.circle_radius = circle_radius
        #self.func = lambda x: distance

    def func(self, pos):
        dsq = None
        if -0.05 <= pos - self.start < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + self.start - pos)**2
        if -0.05 <= self.end - pos < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + pos - self.end)**2

        if dsq is not None:
            dsq = max(dsq, 0)
            return self.distance + (self.circle_radius - np.sqrt(dsq)) * 0.35
        return self.distance

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
        max_segment = 0.005  # 5mm
        profile = rib.profile_2d
        profile_normvectors = PolyLine2D(profile.normvectors)

        start = profile(self.start)
        end = profile(self.end)

        point_range = []
        last_node = None
        for p in profile[start:end]:
            sign = -1 if p[1] > 0 else +1

            if last_node is not None:
                diff = norm(p - last_node) * rib.chord
                if diff > max_segment:
                    segments = int(math.ceil(diff/max_segment))
                    point_range += list(np.linspace(point_range[-1], sign*p[0], segments))[1:]
                else:
                    point_range.append(sign*p[0])
            else:
                point_range.append(sign*p[0])

            last_node = p

        indices = [profile(x) for x in point_range]

        return [(profile[index] - profile_normvectors[index]*self.func(x))*rib.chord for index, x in zip(indices, point_range)]


class FoilCurve(object):
    def __init__(self, front=0, end=0.17):
        self.front = front
        self.end = end

    def get_flattened(self, rib, numpoints=30):
        curve = [
            [self.end, 0.75],
            [self.end-0.05, 1],
            [self.front, 0],
            [self.end-0.05, -1],
            [self.end, -0.75]
        ]
        profile = rib.profile_2d

        cp = [profile.align(point)*rib.chord for point in curve]


        return Bezier(cp).interpolation(numpoints)


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
        circle = Polygon(edges=num_points)(point_1, point_2)[0][1:] # todo: is_center -> true
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
        start2 = profile.cut(gib_arc[0], gib_arc[1], start)
        #print(gib_arc)
        stop = profile.cut(gib_arc[-2], gib_arc[-1], start)
        # Append Profile_List
        gib_arc += profile.get(start2.next()[0], stop.next()[0]).tolist()

        return np.array(gib_arc) * rib.chord


class CellAttachmentPoint(Node):
    def __init__(self, cell, name, cell_pos, rib_pos, force=None):
        super(CellAttachmentPoint, self).__init__(node_type=2)
        self.cell = cell
        self.cell_pos = cell_pos
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

    def __json__(self):
        return {
            "cell": self.cell,
            "cell_pos": self.cell_pos,
            "rib_pos": self.rib_pos,
            "name": self.name,
            "force": self.force
        }

    def get_position(self):
        ik = self.cell.rib1.profile_2d(self.rib_pos)
        self.vec = self.cell.midrib(self.cell_pos)[ik]
        return self.vec

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
                "name": self.name,
                "rib_pos": self.rib_pos,
                "force": self.force}

    def get_position(self):
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec


class RibHole(object):
    def __init__(self, pos, size=0.5, horizontal_shift=0., rotation=0.):
        self.pos = pos
        self.size = size
        self.horizontal_shift = horizontal_shift
        self.rotation = rotation  # rotation about p1

    def get_3d(self, rib, num=20):
        hole = self.get_points(rib, num=num)
        return rib.align_all(set_dimension(hole, 3))

    def get_flattened(self, rib, num=80, scale=True):
        points = self.get_points(rib, num).data
        if scale:
            points *= rib.chord
        return PolyLine2D(points)
        #return Polygon(p1, p2, num=num, scale=self.size, is_center=False)[0]

    def get_points(self, rib, num=80):
        prof = rib.profile_2d
        p1 = prof[prof(self.pos)]
        p2 = prof[prof(-self.pos)]
        poly = Polygon(scale=self.size, edges=num, name="rib_hole")
        return poly(p1, p2, horizontal_shift=self.horizontal_shift, rotation=self.rotation)[0]

    def get_center(self, rib, scale=True):
        prof = rib.profile_2d
        p1 = prof[prof(self.pos)]
        p2 = prof[prof(-self.pos)]
        if scale:
            p1 *= rib.chord
            p2 *= rib.chord
        move_1 = Translation(p1)
        move_2 = Translation((p2 - p1) / 2 * (1 + self.horizontal_shift))
        rot = Rotation(self.rotation)
        return (move_2 * rot * move_1)([0., 0.]) 


class Mylar(object):
    pass

