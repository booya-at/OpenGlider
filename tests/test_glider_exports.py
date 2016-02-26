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
import tempfile
import json

from common import *
from openglider.plots import flatten_glider
from openglider import jsonify
from test_glider import GliderTestClass


class TestGlider(TestCase):
    def setUp(self, a=None):
        self.glider_2d = self.import_glider_2d()
        self.glider = self.glider_2d.get_glider_3d()

    def tempfile(self, name):
        return os.path.join(tempfile.gettempdir(), name)

    @unittest.skip('obsolete')
    def test_import_export_ods(self):
        path = self.tempfile('kite.ods')
        self.glider.export_geometry(path)

    def test_export_obj(self):
        path = self.tempfile('kite.obj')
        self.glider.export_3d(path, midribs=5)

    @unittest.skip('this hangs')
    def test_export_dxf(self):
        path = self.tempfile('kite.dxf')
        self.glider.export_3d(path, midribs=5)

    def test_export_apame(self):
        path = self.tempfile('kite.inp')
        self.glider.export_3d(path, midribs=1)

    def test_export_json(self):
        path = self.tempfile('kite_3d_panels.json')
        data = self.glider.export_3d(path=path, midribs=2, numpoints=10, wake_panels=3, wake_length=0.9)
        with open(path, "w") as outfile:
            json.dump(data, outfile, indent=2)

    @unittest.skip("")
    def test_export_plots(self):
        path = self.tempfile('kite_plots.svg')
        dxfile = self.tempfile("kite_plots.dxf")
        ntvfile = self.tempfile("kite_plots.ntv")
        plots = flatten_glider(self.glider)
        all = plots['panels']
        all.join(plots['ribs'])
        all.export_svg(path)
        all.export_dxf(dxfile)
        all.export_ntv(ntvfile)

    def test_export_glider_json(self):
        with open(self.tempfile('kite_3d.json'), "w+") as tmp:
            jsonify.dump(self.glider, tmp)
            tmp.seek(0)
            glider = jsonify.load(tmp)['data']
        self.assertEqualGlider(self.glider, glider)

    def test_export_glider_ods(self):
        path = self.tempfile("kite.ods")
        self.glider_2d.export_ods(path)
        glider_2d_2 = self.glider_2d.import_ods(path)
        self.assertEqualGlider2D(self.glider_2d, glider_2d_2)

    def test_export_glider_json2(self):
        with open(self.tempfile("kite_2d.json"), "w+") as outfile:
            jsonify.dump(self.glider_2d, outfile)
            outfile.seek(0)
            glider = jsonify.load(outfile)['data']
        self.assertEqualGlider2D(self.glider_2d, glider)




if __name__ == '__main__':
    unittest.main(verbosity=2)