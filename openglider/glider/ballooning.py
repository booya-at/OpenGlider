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

import numpy

import openglider
from openglider.vector.spline import BSpline
from openglider.vector.interpolate import Interpolation


class ArcSinc:
    def __init__(self, numpoints=openglider.config['asinc_interpolation_points']):
        self.start = 0.
        self.end = numpy.pi
        self.arsinc = None
        self.interpolate(numpoints)

    def __call__(self, val):
        if self.arsinc is None:
            self.interpolate()
        return self.arsinc(val)

    def interpolate(self, numpoints):
        data = []

        for i in range(numpoints + 1):
            phi = self.end + (i * 1. / numpoints) * (self.start - self.end)  # reverse for interpolation (increasing x_values)
            data.append([numpy.sinc(phi / numpy.pi), phi])

        self.arsinc = Interpolation(data)

    @property
    def numpoints(self):
        return len(self.arsinc.x)

    @numpoints.setter
    def numpoints(self, numpoints):
        self.interpolate(numpoints)


class Ballooning(object):
    arcsinc = ArcSinc()

    def __init__(self, f_upper, f_lower):
        self.upper = f_upper
        self.lower = f_lower

    def __json__(self):
        return {'f_upper': self.upper,
                'f_lower': self.lower}

    def __getitem__(self, xval):
        """Get Ballooning Value (%) for a certain XValue"""
        if -1 <= xval < 0:
            #return self.upper.xpoint(-xval)[1]
            return self.upper(-xval)
        elif 0 <= xval <= 1:
            #return -self.lower.xpoint(xval)[1]
            return self.lower(xval)
        else:
            raise ValueError("Ballooning only between -1 and 1")

    def __call__(self, arg):
        """Get Ballooning Arc (phi) for a certain XValue"""
        return self.phi(1. / (self[arg] + 1))

    def __add__(self, other):
        """Add another Ballooning to this one, needed for merging purposes"""
        upper = []
        for point in self.upper.data:
            upper.append([point[0], point[1]+other.upper(point[0])])
        lower = []
        for point in self.lower.data:
            lower.append([point[0], point[1]+other.lower(point[0])])

        return Ballooning(Interpolation(upper), Interpolation(lower))

    def __imul__(self, val):
        for point in self.upper.data:
            point[1] *= val
        for point in self.lower.data:
            point[1] *= val
        return self

    def __mul__(self, value):
        """Multiply Ballooning With a Value"""
        new = self.copy()
        new *= value
        return new

    def copy(self):
        return copy.deepcopy(self)

    @classmethod
    def phi(cls, *baloon):
        """
        Return the angle of the piece of cake.
        b/l=R*phi/(R*Sin(phi)) -> Phi=arsinc(l/b)
        """
        return cls.arcsinc(baloon)

    def mapx(self, xvals):
        return [self[i] for i in xvals]

    @property
    def amount_maximal(self):
        return max(max([p[1] for p in self.upper]), max([p[1] for p in self.lower]))

    @property
    def amount_integral(self):
        # Integration of 2-points always:
        amount = 0
        for curve in [self.upper, self.lower]:
            for p1, p2 in zip(curve[:-1], curve[1:]):
                # points: (x1,y1), (x2,y2)
                #     _ p2
                # p1_/ |
                #  |   |
                #  |___|
                amount += (p1[1] + (p2[1]-p1[1])/2) * (p2[0]-p1[0])
        return amount / 2

    @amount_maximal.setter
    def amount_maximal(self, amount):
        factor = float(amount) / self.amount_maximal
        self.upper.scale(1, factor)
        self.lower.scale(1, factor)#


class BallooningBezier(Ballooning):
    def __init__(self, upper=None, lower=None, name="ballooning"):
        super(BallooningBezier, self).__init__(None, None)
        upper = upper or [[0, 0], [0.1, 0], [0.2, 0.14], [0.8, 0.14], [0.9, 0], [1, 0]]
        lower = lower or [[0, 0], [0.1, 0], [0.2, 0.14], [0.8, 0.14], [0.9, 0], [1, 0]]
        self.upper_spline = BSpline(upper)
        self.lower_spline = BSpline(lower)
        self.name = name
        self.apply_splines()

    def __json__(self):
        return {"upper": [p.tolist() for p in self.upper_spline.controlpoints],
                "lower": [p.tolist() for p in self.lower_spline.controlpoints]}

    @property
    def points(self):
        upper = list(self.upper_spline.get_sequence())
        lower = map(lambda x: [x[0], -x[1]], self.lower_spline.get_sequence()[::-1])
        return upper + lower

    def apply_splines(self):
        self.upper = self.upper_spline.interpolation()
        self.lower = self.lower_spline.interpolation()

    def __imul__(self, factor):  # TODO: Check consistency
        """Multiplication of BezierBallooning"""
        # Multiplicate as normal interpolated ballooning, then refit
        Ballooning.__imul__(self, factor)
        # print("JO")
        self.upper_spline.fit(self.upper.data)
        self.lower_spline.fit(self.lower.data)
        return self

    @property
    def numpoints(self):
        return len(self.upper)

    @numpoints.setter
    def numpoints(self, numpoints):
        Ballooning.__init__(self, self.upper_spline.interpolation(numpoints), self.lower_spline.interpolation(numpoints))

    @property
    def controlpoints(self):
        return self.upper_spline.controlpoints, self.lower_spline.controlpoints

    @controlpoints.setter
    def controlpoints(self, controlpoints):
        upper, lower = controlpoints
        if upper is not None:
            self.upper_spline.controlpoints = upper
        if lower is not None:
            self.lower_spline.controlpoints = lower
        Ballooning.__init__(self, self.upper_spline.interpolation(), self.lower_spline.interpolation())


