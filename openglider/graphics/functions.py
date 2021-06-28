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


import vtk
import numpy as np

from openglider.vector import depth
# Quick graphics lib to imitate mathematicas graphics functions


def tofloat(lst):
    if isinstance(lst, list):
        return map(tofloat, lst)
    else:
        return float(lst)


def __isintlist(arg):
    if depth(arg) > 1:
        return max([__isintlist(i) for i in arg])
    else:
        if isinstance(arg, int):
            return 0
        else:
            return 1


def _isintlist(arg):
    if __isintlist(arg) == 0:
        return True
    else:
        return False



