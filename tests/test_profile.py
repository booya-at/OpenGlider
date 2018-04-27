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

import os
import tempfile
import unittest
from common import import_dir
from openglider.airfoil import Profile2D
from test_vector import *

TEMPDIR =  tempfile.gettempdir()

class TestProfile(unittest.TestCase):
    def setUp(self):
        self.prof = Profile2D.import_from_dat(import_dir + "/testprofile.dat")
        self.prof.normalize()

    def test_numpoints(self):
        num = random.randint(4, 500)
        self.prof.numpoints = num
        self.assertEqual(num + 1 - num % 2, self.prof.numpoints)

    def test_export(self):
        path = os.path.join(TEMPDIR, "prof.dat")
        self.prof.export_dat(path)

    def test_profilepoint(self):
        x = random.random() * random.randint(-1, 1)
        self.assertAlmostEqual(abs(x), self.prof.profilepoint(x)[0])

    def test_multiplication(self):
        factor = random.random()
        other = self.prof * factor
        self.assertAlmostEqual(other.thickness, self.prof.thickness * factor)
        other *= 1. / factor
        self.assertAlmostEqual(other.thickness, self.prof.thickness)

    def test_area(self):
        factor = random.random()
        self.assertAlmostEqual(factor * self.prof.area, (self.prof * factor).area)

    def test_compute_naca(self):
        numpoints = random.randint(10, 200)
        thickness = random.randint(8, 20)
        m = random.randint(1, 9) * 1000  # Maximum camber position
        p = random.randint(1, 9) * 100  # Maximum thickness position
        prof = Profile2D.compute_naca(naca=m+p+thickness, numpoints=numpoints)
        self.assertAlmostEqual(prof.thickness*100, thickness, 0)

    def test_add(self):
        other = self.prof.copy()
        other = self.prof + other
        self.assertAlmostEqual(2*self.prof.thickness, other.thickness)

    def test_mul(self):
        self.prof *= 0

    def test_thickness(self):
        val = random.random()
        thickness = self.prof.thickness
        self.prof.thickness *= val
        self.assertAlmostEqual(self.prof.thickness, thickness*val)

    @unittest.skip("whatsoever!")
    def test_camber(self):
        val = random.random()
        camber = max(self.prof.camber[:, 1])
        self.prof.camber = camber*val
        self.assertAlmostEqual(self.prof.camber, camber*val)

    def test_contains_point(self):
        allowance = random.random()*0.1
        prof = self.prof.copy()
        prof2 = self.prof.copy()
        prof2.add_stuff(2*allowance)
        self.prof.add_stuff(allowance)
        self.prof.close()
        # prof<self.prof<prof2
        #print("jo")
        for p in prof.data:
            self.assertTrue(self.prof.contains_point(p))
        for p in prof2.data:
            self.assertFalse(self.prof.contains_point(p))

    @unittest.skip("redundant")
    def test_numpoints2(self):
        print("len: ", len(self.prof.data), len(self.prof._rootprof.data))
        self.prof.numpoints = 20
        print("len2: ", len(self.prof.data), len(self.prof._rootprof.data))


if __name__ == '__main__':
    unittest.main(verbosity=2)
