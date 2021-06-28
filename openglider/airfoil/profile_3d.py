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
import euklid

from openglider.utils.cache import cached_property
from openglider.airfoil import Profile2D

class Profile3D:
    def __init__(self, data, name="unnamed"):
        self.curve = euklid.vector.PolyLine3D(data)
        self.name = name

    def __getitem__(self, ik):
        return self.curve.get(ik)
    
    def get_positions(self, start, stop):
        return self.curve.get_positions(start, stop)
    
    def get(self, start, stop=None):
        if stop is None:
            return self.curve.get(start)
            
        return self.curve.get(start, stop)

    @cached_property('self')
    def noseindex(self):
        p0 = self.curve.nodes[0]
        max_dist = 0
        noseindex = 0
        for i, p1 in enumerate(self.curve.nodes):
            diff = (p1 - p0).length()
            if diff > max_dist:
                noseindex = i
                max_dist = diff
        return noseindex

    @cached_property('self')
    def projection_layer(self):
        """
        Projection Layer of profile_3d
        """
        p1 = self.curve.nodes[0]
        diff = [p - p1 for p in self.curve.nodes]



        xvect = diff[self.noseindex].normalized() * -1
        yvect = euklid.vector.Vector3D([0, 0, 0])

        for i in range(len(diff)):
            sign = 1 - 2 * (i > self.noseindex)
            yvect = yvect + (diff[i] - xvect * xvect.dot(diff[i])) * sign

        yvect = yvect.normalized()

        return euklid.plane.Plane(self.curve.nodes[self.noseindex], xvect, yvect)

    def flatten(self):
        """Flatten the airfoil and return a 2d-Representative"""
        layer = self.projection_layer
        return Profile2D([layer.project(p) for p in self.curve.nodes],
                         name=self.name or 'profile' + "_flattened")

    @cached_property('self')
    def normvectors(self):
        layer = self.projection_layer
        profnorm = layer.normvector

        get_normvector = lambda x: x.cross(profnorm).normalized()

        vectors = [get_normvector(self.curve.nodes[1] - self.curve.nodes[0])]
        for i in range(1, len(self.curve.nodes) - 1):
            vectors.append(get_normvector(
                (self.curve.nodes[i + 1] - self.curve.nodes[i]).normalized() +
                (self.curve.nodes[i] - self.curve.nodes[i - 1]).normalized()
                ))
        vectors.append(get_normvector(self.curve.nodes[-1] - self.curve.nodes[-2]))

        return vectors

    @property
    def tangents(self):
        return self.curve.get_tangents()