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
from openglider.vector.functions import norm, normalize
from openglider.vector.polyline import PolyLine, PolyLine2D


__author__ = 'simon'
import unittest
import random
from openglider import vector

def makelists(self, dim):
    self.vectors = []
    self.sums = []
    numlists = 100
    self.numpoints = numpoints = 100
    for i in range(numlists):
        #make the points
        pointlist = []
        for u in range(numpoints):
            pointlist.append([random.random() * 100 for i in range(dim)])
        self.vectors.append(PolyLine(pointlist))


class TestVector3D(unittest.TestCase):

    def setUp(self, dim=3):
        makelists(self, dim)

    def test_extend_total(self):
        #Sum up the length of the list and check
        for thalist in self.vectors:
            total = 0
            for i in range(len(thalist) - 2):
                total += norm(thalist[i] - thalist[i + 1])
                # First Test:
            i2 = thalist.extend(0, total)
            self.assertAlmostEqual(i2, len(thalist) - 2)

            # Second Test:
            self.assertAlmostEqual(total, thalist.get_length(0, len(thalist) - 2))

    def test_extend_case_within(self):
        #First point within the list
        for thalist in self.vectors:
            start = random.random() * self.numpoints
            leng = random.random() * 100 - 50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start=" + str(start) + " and leng=" + str(leng) +
                                   "\nresult: i2=" + str(new) + " leng2=" + str(leng2) +
                                   " dist=" + str(norm(thalist[start] - thalist[new])))

    def test_extend_case_before(self):
        #First Point before Start
        for thalist in self.vectors:
            start = -random.random() * 30
            leng = random.random() * 100 - 50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start=" + str(start) + " and leng=" + str(leng) +
                                   "\nresult: i2=" + str(new) + " leng2=" + str(leng2) +
                                   " dist=" + str(norm(thalist[start] - thalist[new])))

    def test_extend_case_afterend(self):
        #First Point further than the end
        for thalist in self.vectors:
            start = self.numpoints + random.random() * 50
            leng = random.random() * 100 - 50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start=" + str(start) + " and leng=" + str(leng) +
                                   "\nresult: i2=" + str(new) + " leng2=" + str(leng2) +
                                   " dist=" + str(norm(thalist[start] - thalist[new])))


class TestVector2D(TestVector3D):
    def setUp(self, dim=2):
        makelists(self, dim)
        #TestVector3D.setUp(self, dim)
        self.vectors = [PolyLine2D(i.data[:]) for i in self.vectors]

    #@unittest.skip("temp")
    def test_A_selfcheck(self):
        for thalist in self.vectors:
            thalist.check()

    def test_normvectors(self):
        for thalist in self.vectors:
            i = random.randint(1, len(thalist)-3)  # TODO: Fix for other values
            normv = thalist.normvectors
            self.assertAlmostEqual(normv[i].dot(thalist[i+1]-thalist[i-1]), 0)

    def test_shift(self):
        for thalist in self.vectors:
            amount = random.random()
            thalist.add_stuff(amount)

    def test_Cut(self):
        for thalist in self.vectors:
            i = random.randint(1, len(thalist)-3)
            normv = thalist.normvectors
            dirr = normalize(normv[i])
            #dirr = vector.normalize(normv[i-i % 1])+vector.normalize(normv[i - i % 1 + 1])
            dirr *= 0.001

            p1 = thalist[i]+dirr
            p2 = thalist[i]-dirr
            neu = thalist.cut(p1, p2, i-1)
            #self.assertAlmostEqual(i, neu[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)