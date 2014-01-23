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
import math
import os
import sys

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider import glider
import openglider.Graphics
from openglider.Vector import norm

testfolder = os.path.dirname(os.path.abspath(__file__))


def odf_import_visual_test(path=testfolder + '/demokite.ods'):
    glider1 = glider.Glider()
    glider1.import_geometry(path)
    glider1.close_rib(-1)  # Stabi
    glider1 = glider1.copy_complete()
    glider1.recalc()
    # TODO: Miniribs for mirrored cells fail
    #new_glider.cells[0].miniribs.append(MiniRib(0.5, 0.7, 1))

    # 3D-OUTPUT
    (polygons, points) = glider1.return_polygons(5)
    polygons = [openglider.Graphics.Polygon(polygon) for polygon in polygons]
    polygons.append(openglider.Graphics.Axes(size=1.2))
    openglider.Graphics.Graphics3D(polygons, points)

    # Shape-Output
    left, right = glider1.shape()
    left.rotate(math.pi/2)
    right.rotate(math.pi/2, [0, 0])
    openglider.Graphics.Graphics2D([openglider.Graphics.Line(left.data),
                                    openglider.Graphics.Line([left.data[-1], right.data[-1]]),
                                    openglider.Graphics.Line(right.data),
                                    openglider.Graphics.Line([left.data[0], right.data[0]])])




if __name__ == "__main__":
    odf_import_visual_test()