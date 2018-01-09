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
from __future__ import division
import numpy as np

from openglider.utils.cache import cached_property
from openglider.vector import Plane
from openglider.vector.functions import norm, normalize
from openglider.vector.polyline import PolyLine
from openglider.airfoil import Profile2D


class Profile3D(PolyLine):
    @cached_property('self')
    def noseindex(self):
        p0 = self.data[0]
        max_dist = 0
        noseindex = 0
        for i, p1 in enumerate(self.data):
            diff = norm(p1 - p0)
            if diff > max_dist:
                noseindex = i
                max_dist = diff
        return noseindex

    @cached_property('self')
    def projection_layer(self):
        """
        Projection Layer of profile_3d
        """
        p1 = self.data[0]
        diff = [p - p1 for p in self.data]

        xvect = normalize(-diff[self.noseindex])
        yvect = np.array([0, 0, 0])

        for i in range(len(diff)):
            sign = 1 - 2 * (i > self.noseindex)
            yvect = yvect + sign * (diff[i] - xvect * xvect.dot(diff[i]))

        yvect = normalize(yvect)
        return Plane(self.data[self.noseindex], xvect, yvect)

    def flatten(self):
        """Flatten the airfoil and return a 2d-Representative"""
        layer = self.projection_layer
        return Profile2D([layer.projection(p) for p in self.data],
                         name=self.name or '' + "_flattened")

    @cached_property('self')
    def normvectors(self):
        layer = self.projection_layer
        profnorm = layer.normvector
        get_normvector = lambda x: normalize(np.cross(x, profnorm))

        vectors = [get_normvector(self.data[1] - self.data[0])]
        for i in range(1, len(self.data) - 1):
            vectors.append(get_normvector(
                normalize(self.data[i + 1] - self.data[i]) +
                normalize(self.data[i] - self.data[i - 1])))
        vectors.append(get_normvector(self.data[-1] - self.data[-2]))

        return vectors

    @property
    def tangents(self):
        second = self.data[0]
        third = self.data[1]
        tangents = [normalize(third - second)]
        for element in self.data[2:]:
            first = second
            second = third
            third = element
            tangent = np.array([0, 0, 0])
            for vec in [third-second, second-first]:
                try:
                    tangent = tangent + normalize(vec)
                except ValueError:  # zero-length vector
                    pass
            tangents.append(tangent)
        tangents.append(normalize(third - second))
        return tangents