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
import tempfile
from openglider.jsonify import load
from openglider.plots import create_svg, flatten_glider, flattened_cell
from openglider.glider.cell_elements import Panel
from openglider.graphics import Line, Graphics2D, Red, Graphics3D

class TestGlider(unittest.TestCase):
    def setUp(self):
        with open("./fehler_nahtzugabe.gl3d.json", "r") as importfile:
            self.glider = load(importfile)["data"]
            for i, cell in enumerate(self.glider.cells):
                cell.panels = [Panel([-1, -1, 3, 0.012], [1, 1, 3, 0.012], i)]
            self.plots = flatten_glider(self.glider)


    def file(self, suffix):
        f = tempfile.NamedTemporaryFile(suffix=suffix)
        return f

    # def test_flatten_svg(self):
    #     path = self.file('.svg').name
    #     all = self.plots['panels']
    #     all.insert(self.plots['ribs'])
    #     create_svg(all, path)

    def test_flatten_cell(self):
        layers={}
        l = self.plots["panels"].parts[-1].layer_dict
        for name, layer in l.iteritems():
            layers.setdefault(name, [])
            layers[name] += layer

        Graphics3D([Line(l) for l in layers['OUTER_CUTS']] +
                   [Line(l) for l in layers['SEWING_MARKS']])

if __name__ == '__main__':
    unittest.main(verbosity=2)