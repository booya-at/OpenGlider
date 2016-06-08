import unittest

import openglider
from openglider.plots import DrawingArea
from openglider.plots.glider import RibPlot




class RibTest(unittest.TestCase):
    def setUp(self):
        self.glider_2d = openglider.load("../common/glider2d.json")
        self.glider_3d = self.glider_2d.get_glider_3d()

    def test_rib(self):
        ribmaker = RibPlot(self.glider_3d.ribs[0])
        pp = ribmaker.flatten(self.glider_3d)
        DrawingArea([pp]).export_svg("/tmp/rib.svg")