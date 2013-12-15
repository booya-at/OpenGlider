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
from openglider.Ribs import MiniRib
import os
import openglider.Graphics
__author__ = 'simon'
testfolder = os.path.dirname(os.path.abspath( __file__ ))
import unittest

from openglider import glider

class test_glider_class(unittest.TestCase):
    def __init__(self):
        unittest.TestCase.__init__(self)
        self.glider = glider.Glider()
        self.glider.import_from_file(testfolder+'/demokite.ods')

    def setUp(self):
        pass

    def test_import_export_ods(self):
        path = '/tmp/daweil.ods'
        self.assertTrue(self.glider.export(path))
        new_glider = glider.Glider()
        self.assertTrue(new_glider.import_from_file(path))
        #self.assertEqual(new_glider, self.glider)


def odf_import_visual_test(path='/home/simon/OpenGlider/tests/demokite.ods'):
    glider1 = glider.Glider()
    glider1.import_from_file(path)
    glider1.close_rib(-1)  # Stabi
    glider2 = glider1.copy()
    glider2.mirror()
    glider2.cells[0].rib2 = glider1.cells[0].rib1  # remove redundant rib-copy
    glider1.cells = glider2.cells[::-1] + glider1.cells  # start from last mirrored towards last normal
    glider1.recalc()
    # TODO: Miniribs for mirrored cells fail
    #new_glider.cells[0].miniribs.append(MiniRib(0.5, 0.7, 1))
    (polygons, ribs) = glider1.return_polygons(20)
    polygons = [openglider.Graphics.Polygon(polygon) for polygon in polygons]
    openglider.Graphics.Graphics3D(polygons, ribs)

odf_import_visual_test()
