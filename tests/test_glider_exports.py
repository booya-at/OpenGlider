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
import sys
import os
from openglider.plots import flatten_glider

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider import glider
import openglider.glider.plots

testfolder = os.path.dirname(os.path.abspath(__file__))


class TestGlider(unittest.TestCase):
    #def __init__(self):
    #    unittest.TestCase.__init__(self)

    def setUp(self):
        self.glider = glider.Glider()
        self.glider.import_geometry(testfolder + '/demokite.ods')

    def test_import_export_ods(self):
        path = '/tmp/daweil.ods'
        self.glider.export_geometry(path)
        #new_glider = glider.Glider()
        #self.assertTrue(new_glider.import_from_file(path))
        #self.assertEqual(new_glider, self.glider)

    def test_export_obj(self):
        path = '/tmp/Booya.obj'
        self.glider.export_3d(path, midribs=5)

    def test_export_dxf(self):
        path = '/tmp/booya.dxf'
        self.glider.export_3d(path, midribs=5)

    def test_export_apame(self):
        path = '/tmp/booya.inp'
        self.glider.export_3d(path, midribs=1)

    def test_export_plots(self):
        path = '/tmp/plots.dxf'
        self.glider.recalc()
        flatten_glider(self.glider, path)


if __name__ == '__main__':
    unittest.main(verbosity=2)