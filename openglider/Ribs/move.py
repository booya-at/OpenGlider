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


from openglider.Vector import rotation_3d
import math
###########entweder klasse oder funktion die funktion erzeugt


def rotation(aoa, arc, zrot):
    """Rotation Matrix for Ribs, aoa, arcwide-angle and glidewise angle in radians"""
    # Rotate Arcangle, rotate from lying to standing (x-z)
    rot = rotation_3d(-arc + math.pi / 2, [-1, 0, 0])
    axis = rot.dot([0, 0, 1])
    rot = rotation_3d(aoa, axis).dot(rot)
    axis = rot.dot([0, 1, 0])
    rot = rotation_3d(zrot, axis).dot(rot)
    #rot = rotation_3d(-math.pi/2, [0, 0, 1]).dot(rot)

    return rot