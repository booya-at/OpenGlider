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

import unittest
import numpy
from openglider.utils.distribution import Distribution


class TestProfile(unittest.TestCase):
    def setUp(self):
        self.fixpoints = [-0.9, -0.7, -0.4, 0.1, 0.5, 0.9]
        self.dist_types = "cos, cos_2, nose_cos, const"

    def test_is_in_list(self):
        for typ in self.dist_types:
            a = distribution(
                numpoints=30,
                fix_points=self.fixpoints,
                dist_type=typ
                )
            for point in self.fixpoints:
                self.assertAlmostEqual(min(numpy.abs(a.data - point)), 0)



if __name__ == '__main__':
    unittest.main(verbosity=2)
