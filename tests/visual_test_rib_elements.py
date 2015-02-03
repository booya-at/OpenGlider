import random
import unittest

from visual_test_glider import GliderTestClass
import common

import openglider
from openglider.glider.rib_elements import RibHole, RigidFoil, GibusArcs, Mylar
import openglider.graphics as Graph


class TestRibElements(GliderTestClass):
    def test_gibus_arcs(self):
        rib_no = random.randint(0, len(self.glider.ribs)-1)
        gibus_arc = GibusArcs(rib=self.glider.ribs[rib_no], position=.15, size=0.02)
        thalist = gibus_arc.get_3d(num_points=10)

        Graph.Graphics([Graph.Line(self.glider.ribs[rib_no].profile_3d.data),
                        Graph.Polygon(thalist)])

    def test_hole(self):
        rib_no = random.randint(0, len(self.glider.ribs)-1)
        hole = RibHole(self.glider.ribs[rib_no], 0.2)
        thalist = hole.get_3d()
        Graph.Graphics([Graph.Line(self.glider.ribs[rib_no].profile_3d.data),
                        Graph.Polygon(thalist)])


if __name__ == '__main__':
    unittest.main()