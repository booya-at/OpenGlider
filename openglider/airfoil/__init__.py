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
from openglider.airfoil.profile_2d import Profile2D
from openglider.airfoil.profile_3d import Profile3D
from openglider.airfoil.parametric import BezierProfile2D


def get_x_value(x_value_list, x):
    """
    Get position of x in a list of x_values
    zb get_x_value([1,2,3],1.5)=0.5
    """
    for i in range(len(x_value_list) - 1):
        if x_value_list[i + 1] >= x or i == len(x_value_list) - 2:
            return i - (x_value_list[i] - x) / (x_value_list[i + 1] - x_value_list[i])
