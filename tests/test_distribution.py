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

import numpy

from openglider.utils.distribution import Distribution


class TestProfile(unittest.TestCase):
    num_dist = 40
    num_fixed = 10

    def setUp(self):
        self.fixpoints = [(random.random()-0.5)*2 for _ in range(self.num_fixed)]

        self.dist_types = "cos, cos_2, nose_cos, const"

    def test_is_in_list(self):
        for typ in self.dist_types:
            a = Distribution.new(
                numpoints=self.num_dist,
                fixed_nodes=self.fixpoints,
                dist_type=typ
                )
            for fixed in self.fixpoints:
                self.assertAlmostEqual(min(numpy.abs(a.data - fixed)), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
