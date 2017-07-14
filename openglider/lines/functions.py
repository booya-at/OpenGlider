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
import numpy
import traceback


def proj_force(force, vec):
    proj = numpy.dot(vec, force)
    try:
        assert proj**2 >= 0.00001
    except AssertionError as e:
        print("shit", vec, force, proj)
        return None
    return numpy.dot(force, force) / proj


def proj_to_surface(vec, n_vec):
    return vec - numpy.array(n_vec) * numpy.dot(n_vec, vec) / numpy.dot(n_vec, n_vec)
