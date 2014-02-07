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


path = testfolder + '/demokite.ods'
glider1 = glider.Glider()
glider1.import_geometry(path)
glider1 = glider1.copy_complete()
glider1.recalc()

rib1 = glider1.ribs[1].profile_2d
rib2 = glider1.cells[0].midrib(0.5).flatten()
rib2.normalize()
rib1.normalize()

openglider.Graphics.Graphics2D([openglider.Graphics.Line(rib1.data),
                                openglider.Graphics.Line(rib2.data)])