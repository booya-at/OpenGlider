import unittest

import openglider
import openglider.plots
import openglider.plots.glider
from common import TestCase

class TestPlots(TestCase):
    def setUp(self, complete=True):
        self.glider_2d = self.import_glider_2d()
        self.glider_3d = self.glider_2d.get_glider_3d()
        self.plotmaker = openglider.plots.PlotMaker(self.glider_3d)

    @unittest.skip("not working")
    def test_patterns_panels(self):
        self.plotmaker.get_panels()
        dwg = self.plotmaker.get_all_stacked()["panels"]
        dwg.export_dxf("/tmp/test_panels.dxf")

    def test_patterns_dribs(self):
        self.plotmaker.get_dribs()
        dwg = self.plotmaker.get_all_stacked()["dribs"]
        dwg.export_dxf("/tmp/test_dribs.dxf")

    def test_patterns_ribs(self):
        self.plotmaker.get_ribs()
        dwg = self.plotmaker.get_all_stacked()["ribs"]
        dwg.export_dxf("/tmp/test_ribs.dxf")

if __name__ == "__main__":
    unittest.main()