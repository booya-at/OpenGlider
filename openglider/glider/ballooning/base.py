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
import copy

import numpy as np
import euklid

import openglider


class ArcSinc:
    def __init__(self):
        self.start = 0.
        self.end = np.pi
        self.arsinc = None

    def __call__(self, val):
        if self.arsinc is None:
            self.interpolate(openglider.config['asinc_interpolation_points'])
        return self.arsinc.get_value(val)

    def interpolate(self, numpoints):
        data = []

        for i in range(numpoints + 1):
            phi = self.end + (i * 1. / numpoints) * (self.start - self.end)  # reverse for interpolation (increasing x_values)
            data.append([np.sinc(phi / np.pi), phi])

        self.arsinc = euklid.vector.Interpolation(data)

    @property
    def numpoints(self):
        return len(self.arsinc.data)

    @numpoints.setter
    def numpoints(self, numpoints):
        self.interpolate(numpoints)


class BallooningBase():
    arcsinc = ArcSinc()

    def __call__(self, xval):
        return self.get_phi(xval)

    def __getitem__(self, xval):
        raise NotImplementedError()

    def get_phi(self, xval) -> float:
        """Get Ballooning Arc (phi) for a certain XValue"""
        return self.phi(1. / (self[xval] + 1))

    def get_tension_factor(self, xval) -> float:
        """Get the tension due to ballooning"""
        value =  2. * np.tan(self.get_phi(xval))
        if 0. in value:
            return value
        else:
            return 1. / value

    @classmethod
    def phi(cls, baloon) -> float:
        """
        Return the angle of the piece of cake.
        b/l=R*phi/(R*Sin(phi)) -> Phi=arsinc(l/b)
        """
        return cls.arcsinc(baloon)


