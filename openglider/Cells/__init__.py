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


__author__ = 'simon'
#import openglider.Ribs as Ribs
import numpy
from ..Vector import normalize, norm
from ..Profile import Profile3D
from ..Ribs import Rib
#from ..Utils import Ballooning
import math
from openglider.Utils.Ballooning import arsinc


class BasicCell(object):
    def __init__(self, prof1=Profile3D(), prof2=Profile3D(), ballooning=None):
        self.prof1 = prof1
        self.prof2 = prof2

        self._phi = ballooning  # ballooning arcs
        self._cosphi = self._radius = None
        self._normvectors = None

    def point_basic_cell(self, y=0, i=0, k=0):
        ##round ballooning
        return self.midrib_basic_cell(y).point((i, k))

    def midrib_basic_cell(self, y, ballooning=True):
        if y == 0:              # left side
            return self.prof1
        elif y == 1:            # right side
            return self.prof2
        else:                   # somewhere
            #self._checkxvals()
            midrib = []
            prof1 = self.prof1.data
            prof2 = self.prof2.data

            _horizontal = lambda _y, j: prof1[j] + _y * (prof2[j] - prof1[j])

            if ballooning:
                self._calcballooning()

                def _vertical(_y, j):
                    r = self._radius[j]
                    if r > 0:
                        cosphi = self._cosphi[j]
                        d = prof2[j] - prof1[j]
                        #phi=math.asin(norm(d)/(2*r)*(x-1/2)) -> cosphi=sqrt(1-(norm(d)/r*(x+1/2))^2
                        cosphi2 = math.sqrt(1 - (norm(d) * (0.5 - _y) / r) ** 2)
                        return self.normvectors[j] * (cosphi2 - cosphi) * r
                    else:
                        return numpy.array([0, 0, 0])
            else:
                def _vertical(_y, j):
                    return numpy.array([0, 0, 0])

            for i in range(len(self.prof1.data)):  # Arc -> phi(bal) -> r  # oder so...
                midrib.append(_horizontal(y, i)+_vertical(y, i))
            return Profile3D(midrib)

    def recalc(self):
        # Clear everything
        self._normvectors = None
        self._cosphi = None
        self._radius = None
        self._calcballooning()

    def __get_normvectors(self, j=None):
        if not self._normvectors:
            prof1 = self.prof1.data
            prof2 = self.prof2.data
            p1 = self.prof1.tangents()
            p2 = self.prof2.tangents()
            # cross differenzvektor, tangentialvektor
            self._normvectors = []
            for i in range(len(p1)):
                self._normvectors.append(normalize(numpy.cross(p1[i] + p2[i], prof1[i] - prof2[i])))
        if j:
            return self._normvectors[j]
        else:
            return self._normvectors

    def _calcballooning(self):
        if not self._cosphi and not self._radius:  # See sketches in Doc; cosphi and cake-Radius
            self._cosphi = []
            self._radius = []
            if len(self._phi) == len(self.prof1.data) == len(self.prof2.data):
                for i in range(len(self._phi)):
                    if round(self._phi[i], 5) > 0:
                        self._cosphi.append(numpy.cos(self._phi[i]))
                        self._radius.append(
                            norm(self.prof1.data[i] - self.prof2.data[i]) / (2 * numpy.sin(self._phi[i])))
                    else:
                        self._cosphi.append(0)
                        self._radius.append(0)
            else:
                raise ValueError("length of ballooning/profile data unequal")

    normvectors = property(__get_normvectors)


# Ballooning is considered to be arcs, following two simple rules:
# 1: x1 = x*d
# 2: x2 = R*normvekt*(cos(phi2)-cos(phi)
# 3: norm(d)/r*(1-x) = 2*sin(phi(2))

class Cell(BasicCell):
    #TODO: cosmetics
    def __init__(self, rib1=Rib(), rib2=Rib(), miniribs=None):
        self.rib1 = rib1
        self.rib2 = rib2
        self.miniribs = miniribs
        self._yvalues = []
        self._cells = []
        BasicCell.__init__(self, self.rib1.profile_3d, self.rib2.profile_3d, [])

    def recalc(self):
        if not self.rib2.profile_2d.numpoints == self.rib1.profile_2d.numpoints:
            raise ValueError("Unequal length of Cell-Profiles")
        xvalues = self.rib1.profile_2d.x_values
        phi = [self.rib1.ballooning(x) + self.rib2.ballooning(x) for x in xvalues]
        BasicCell.__init__(self, self.rib1.profile_3d, self.rib2.profile_3d, phi)
        BasicCell.recalc(self)
        #Map Ballooning

        if not self.miniribs:  # In case there is no midrib, The Cell represents itself!
            self._cells = [self]  # The cell itself is its cell, clear?
            self._yvalues = [0, 1]
        else:
            self._cells = []
            self._yvalues = [0] + [rib.y_value for rib in self.miniribs] + [1]
            ballooning = [self.rib1.ballooning[x] + self.rib2.ballooning[x] for x in xvalues]
            miniribs = sorted(self.miniribs, key=lambda rib: rib.y_value)  # sort for cell-wide (y) argument.

            first = self.rib1.profile_3d
            for minirib in miniribs:
                big = self.midrib_basic_cell(minirib.y_value, True).data
                small = self.midrib_basic_cell(minirib.y_value, False).data
                points = []

                for i in range(len(big)):  # Calculate Rib
                    fakt = minirib.function(xvalues[i])  # factor ballooned/unb. (0-1)
                    point = small[i] + fakt * (big[i] - small[i])
                    points.append(point)

                minirib.data = points
                second = minirib
                self._cells.append(BasicCell(first, second, []))  # leave ballooning empty
                first = second
            #Last Sub-Cell
            self._cells.append(BasicCell(first, self.rib2.profile_3d, []))

            # Calculate ballooning for each x-value
            # Hamilton Principle:
            #       http://en.wikipedia.org/wiki/Hamilton%27s_principle
            #       http://en.wikipedia.org/wiki/Hamilton%E2%80%93Jacobi_equation
            # b' = b
            # f' = f*(l/l') [f=b/l]
            for i in range(len(first.data)):
                bl = ballooning[i] + 1  # b/l -> *l/lnew
                l = norm(self.rib2.profile_3d.data[i] - self.rib1.profile_3d.data[i])  # L
                lnew = sum([norm(c.prof1.data[i] - c.prof2.data[i]) for c in self._cells])  # L-NEW
                for c in self._cells:
                    c._phi.append(arsinc(lnew/l / bl))  # B/L NEW 1 / (bl * l / lnew)
            for cell in self._cells:
                cell.recalc()

    def point(self, y=0, i=0, k=0):
        return self.midrib(y).point(i, k)

    def midrib(self, y, ballooning=True):
        if len(self._cells) == 1:
            return self.midrib_basic_cell(y, ballooning=ballooning)
        if ballooning:
            i = 0
            while self._yvalues[i + 1] < y:
                i += 1
            cell = self._cells[i]
            xnew = (y - self._yvalues[i]) / (self._yvalues[i + 1] - self._yvalues[i])
            return cell.midrib_basic_cell(xnew)
        else:
            return self.midrib_basic_cell(y, ballooning=False)

    def _calcballooning(self):
        xvalues = self.rib1.profile_2d.x_values
        balloon = [self.rib1.ballooning[i] + self.rib2.ballooning[i] for i in xvalues]
        self._phi = [arsinc(1 / (1 + i)) for i in balloon]
        BasicCell._calcballooning(self)

    def __get_span(self):  # TODO: Maybe use mean length from (1,0), (0,0)
        return norm((self.rib1.pos - self.rib2.pos)*[0, 1, 1])

    def __get_area(self):
        p1_1 = self.rib1.align([0, 0, 0])
        p1_2 = self.rib1.align([1, 0, 0])
        p2_1 = self.rib2.align([0, 0, 0])
        p2_2 = self.rib2.align([1, 0, 0])
        return 0.5*(norm(numpy.cross(p1_2-p1_1, p2_1-p1_1)) + norm(numpy.cross(p2_2-p2_1, p2_2-p1_2)))

    def __get_ar(self):
        return self.span**2/self.area

    span = property(__get_span)
    area = property(__get_area)
    aspect_ratio = property(__get_ar)


"""
    def _checkxvals(self):
        #####TODO: push to normal cell.
        if not numpy.allclose(self.rib1.profile_2d.XValues, self.rib2.profile_2d.XValues):
            self.rib2.profile_2d.XValues = self.rib1.profile_2d.XValues
            self.rib2.ReCalc()
            redo = True
        else:
            redo = False
        if redo or not self.normvectors:
            self.normvectors = [normalize(self.rib1.normvectors[i]+self.rib2.normvectors[i])
                                for i in range(self.rib1.profile_2d.Numpoints)]
            #TODO: map balooning
            """