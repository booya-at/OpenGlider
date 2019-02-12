# ! /usr/bin/python2
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
import os
import random
import sys
import numpy as np


try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
import openglider.graphics
import openglider.graphics as graphics
from openglider.vector.spline import Bezier
from test_glider import GliderTestClass
import unittest


class TestGlider(GliderTestClass):
    def test_show_lastcell(self):
        thaglider = self.glider
        cell = thaglider.cells[-1]
        #print(cell.normvectors)
        openglider.graphics.Graphics([openglider.graphics.Line(cell.rib1.profile_3d.data),
                                      openglider.graphics.Line(cell.rib2.profile_3d.data)])

    @staticmethod
    def show_glider(glider, num=5):
        left = glider.copy()
        right = left.copy()
        right.mirror()
        ribs = left.return_ribs(num)
        polygons = left.return_polygon_indices(ribs)
        points = np.concatenate(ribs)
        objects = []
        objects += [openglider.graphics.Red]
        objects += map(openglider.graphics.Polygon, polygons)
        objects += [openglider.graphics.Green]
        objects += [openglider.graphics.Polygon(rib.profile_3d.data) for rib in right.ribs]
        blue = openglider.graphics.Blue
        objects += map(lambda line: openglider.graphics.Line(line.get_line_points(), colour=blue.colour),
                       left.lineset.lines)

        #objects += [openglider.graphics.Axes(size=1.2)] #, openglider.graphics.Green]
        #objects.append(openglider.graphics.Blue)
        #objects += [openglider.graphics.Line(rib.profile_3d.data) for rib in left.ribs]

        openglider.graphics.Graphics3D(objects, points)

    @unittest.skip('TODO')
    def test_show_shape(self):
        self.glider = self.glider.copy_complete()
        left, right = self.glider.shape_flattened
        #left.rotate(math.pi/2)
        #right.rotate(math.pi/2, [0, 0])
        data = [left,
                right]
        data += [[left[i], right[i]] for i in range(len(left))]
        openglider.graphics.Graphics2D([openglider.graphics.Line(obj) for obj in data])

    @unittest.skip('TODO')
    def test_show_shape_simple(self):
        front, back = self.glider.shape_simple
        openglider.graphics.Graphics2D([openglider.graphics.Line(obj) for obj in (front, back)])

    def test_show_ribs(self):
        #self.glider = self.glider.copy_complete()
        self.glider.mirror()
        openglider.graphics.Graphics([openglider.graphics.Line(rib.profile_3d.data) for rib in self.glider.ribs])

    @unittest.skip("skipped")
    def test_midrib_projection(self):
        num = 3
        data = []
        for i in range(num):
            cell = self.glider.cells[random.randint(0, len(self.glider.cells) - 1)]
            prof = cell.midrib(random.random())
            prof.projection_layer()
            data += [prof.data,
                     [prof.data[0], prof.data[0] + prof.xvect],
                     [prof.data[0], prof.data[0] + prof.yvect]]

        openglider.graphics.Graphics([openglider.graphics.Line(obj) for obj in data])

    def test_midrib_flattened(self):
        num = 2
        cell = self.glider.cells[random.randint(0, len(self.glider.cells) - 1)]
        profs = [cell.rib1.profile_2d.data]
        profs += [cell.midrib(random.random()).flatten().data + [0, (i + 1) * 0.] for i in range(num)]
        openglider.graphics.Graphics2D([openglider.graphics.Line(prof) for prof in profs])

    @unittest.skip('TODO')
    def test_brake(self):
        glider = self.glider
        brake = Bezier([[0., 0.], [1., 0.], [1., -0.2]])
        num = 60
        brakeprof = openglider.airfoil.Profile2D([brake(i / num) for i in reversed(range(num + 1))][:-1] +
                                                 [brake(i / num) for i in range(num + 1)])

        for i, rib in enumerate(glider.ribs):
            rib.profile_2d = rib.profile_2d + brakeprof * (3 * i / len(glider.ribs))

        self.show_glider(glider)

    @unittest.skip('TODO')
    def test_show_glider(self):
        self.show_glider(self.glider)

    @unittest.skip('notyet')
    def test_export_json(self):
        #path = os.tmpfile()
        path = os.tmpnam() + ".json"
        self.glider.export_3d(path)
        import openglider.jsonify

        file = open(path, "r")
        data = openglider.jsonify.load(file)
        graphics.Graphics([graphics.Polygon(panel["node_no"]) for panel in data["panels"] if not panel["is_wake"]],
                          #G.Graphics([G.Polygon(data["panels"][0]["node_no"])],
                          data["nodes"])

    def test_singleskin(self):
        rib = self.glider.ribs[1]
        rib.single_skin_par = {"att_dist": 0.05, "height": 0.5}
        print(rib.get_hull(self.glider))
        graphics.Graphics([openglider.graphics.Line(rib.get_hull(self.glider))])


if __name__ == '__main__':
    unittest.main()