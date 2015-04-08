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
from openglider.plots.part import create_svg
from openglider import jsonify
from test_glider import GliderTestClass


class TestGlider(TestCase):
    def setUp(self, a=None):
        self.glider_2d = self.import_glider_2d()
        self.glider = self.glider_2d.get_glider_3d()

    def tempfile(self, suffix, **kwargs):
        if sys.version.startswith('3'):
            kwargs["mode"] = 'w+'
            kwargs["encoding"] = 'utf-8'
        return tempfile.NamedTemporaryFile(suffix=suffix, **kwargs)

    @unittest.skip('obsolete')
    def test_import_export_ods(self):
        path = self.tempfile('.ods').name
        self.glider.export_geometry(path)

    def test_export_obj(self):
        path = self.tempfile('.obj').name
        self.glider.export_3d(path, midribs=5)

    @unittest.skip('this hangs')
    def test_export_dxf(self):
        path = self.tempfile('.dxf').name
        self.glider.export_3d(path, midribs=5)

    def test_export_apame(self):
        path = self.tempfile('.inp').name
        self.glider.export_3d(path, midribs=1)

    def test_export_json(self):
        path = self.tempfile('.json').name
        data = self.glider.export_3d(path=path, midribs=2, numpoints=10, wake_panels=3, wake_length=0.9)
        with open(path, "w") as outfile:
            json.dump(data, outfile, indent=2)

    def test_export_plots(self):
        path = self.tempfile('.svg').name
        plots = flatten_glider(self.glider)
        all = plots['panels']
        all.insert(plots['ribs'])
        create_svg(all, path)

    def test_export_glider_json(self):
        with self.tempfile('.json') as tmp:
            jsonify.dump(self.glider, tmp)
            tmp.seek(0)
            glider = jsonify.load(tmp)['data']
        self.assertEqualGlider(self.glider, glider)

    def test_export_glider_json2(self):
        path = self.tempfile('.json').name
        with open(path, "w") as outfile:
            jsonify.dump(self.glider, outfile)




if __name__ == '__main__':
    unittest.main(verbosity=2)