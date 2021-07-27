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
import random
import unittest

import numpy as np

from openglider.utils.distribution import Distribution


class TestProfile(unittest.TestCase):
    num_dist = 40
    num_fixed = 10

    def setUp(self):
        self.fixpoints = [(random.random()-0.5)*2 for _ in range(self.num_fixed)]

        self.dist_types = "cos, cos_2, nose_cos, const"
    
    def _get_kwargs(self):
        return {
            "numpoints": self.num_dist,
        }
    
    def _test_dist(self, dist):
        dist.insert_values(self.fixpoints)
        for fixed in self.fixpoints:
            self.assertAlmostEqual(min(np.abs(dist.data - fixed)), 0)

    def test_cos(self):
        dist = Distribution.from_cos_distribution(self.num_dist)
        self._test_dist(dist)

    def test_cos2(self):
        dist = Distribution.from_cos_2_distribution(self.num_dist)
        self._test_dist(dist)

    def test_nose_cos(self):
        dist = Distribution.from_nose_cos_distribution(self.num_dist)
        self._test_dist(dist)

    def test_linear(self):
        dist = Distribution.from_linear(self.num_dist)
        self._test_dist(dist)



if __name__ == '__main__':
    unittest.main(verbosity=2)
