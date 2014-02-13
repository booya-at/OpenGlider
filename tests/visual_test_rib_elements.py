import random
import sys
import os

from visual_test_glider import GliderTestClass

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.glider.rib_elements import RibHole, RigidFoil, GibusArcs, Mylar
import openglider.Graphics as Graph


class TestRibElements(GliderTestClass):
    def test_gibus_arcs(self):
        rib_no = random.randint(0, len(self.glider.ribs)-1)
        gibus_arc = GibusArcs(rib_no=rib_no, position=.15, size=0.02)
        thalist = gibus_arc.get_3d(self.glider, num_points=20)

        Graph.Graphics([Graph.Line(self.glider.ribs[rib_no].profile_3d.data),
                        Graph.Polygon(thalist)])

    def test_hole(self):
        self.glider.recalc()
        rib_no = random.randint(0, len(self.glider.ribs)-1)
        hole = RibHole(rib_no, 0.2)
        thalist = hole.get_3d(self.glider)
        Graph.Graphics([Graph.Line(self.glider.ribs[rib_no].profile_3d.data),
                        Graph.Polygon(thalist)])
