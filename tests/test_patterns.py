import unittest

import tempfile
import os
import openglider
import openglider.plots
import openglider.plots.glider
from common import TestCase


TEMPDIR =  tempfile.gettempdir()

class TestPlots(TestCase):
    def setUp(self, complete=True):
        self.glider_2d = self.import_glider_2d()
        self.glider_3d = self.glider_2d.get_glider_3d()
        self.plotmaker = openglider.plots.PlotMaker(self.glider_3d)

    @unittest.skip("not working")
    def test_patterns_panels(self):
        self.plotmaker.get_panels()
        dwg = self.plotmaker.get_all_stacked()["panels"]
        dwg.export_dxf(os.path.join(TEMPDIR, "test_panels.dxf"))

# Traceback (most recent call last):
#   File "/home/travis/build/booya-at/OpenGlider/tests/test_patterns.py", line 22, in test_patterns_dribs
#     dwg = self.plotmaker.get_all_stacked()["dribs"]
# AttributeError: 'PlotMaker' object has no attribute 'get_all_stacked'
    @unittest.skip("not working")
    def test_patterns_dribs(self):
        self.plotmaker.get_dribs()
        dwg = self.plotmaker.get_all_stacked()["dribs"]
        dwg.export_dxf(os.path.join(TEMPDIR, "test_dribs.dxf"))

    @unittest.skip("not working")
    def test_patterns_ribs(self):
        self.plotmaker.get_ribs()
        dwg = self.plotmaker.get_all_stacked()["ribs"]
        dwg.export_dxf(os.path.join(TEMPDIR, "test_ribs.dxf"))

if __name__ == "__main__":
    unittest.main()