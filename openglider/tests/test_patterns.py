import unittest

import tempfile
import os
import openglider
import openglider.plots
import openglider.plots.glider
from openglider.vector.drawing import Layout
from openglider.tests.common import GliderTestCase


TEMPDIR =  tempfile.gettempdir()

class TestPlots(GliderTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.plotmaker = openglider.plots.PlotMaker(self.glider)

    def test_patterns_panels(self) -> None:
        self.plotmaker.get_panels()
        dwg = self.plotmaker.panels
        dwg.export_dxf(os.path.join(TEMPDIR, "test_panels.dxf"))

    def test_patterns_dribs(self) -> None:
        self.plotmaker.get_dribs()

        columns = [Layout.stack_column(rib, 0.1) for rib in self.plotmaker.dribs.values()]
        dwg = Layout.stack_row(columns, 0.1)
        dwg.export_dxf(os.path.join(TEMPDIR, "test_dribs.dxf"))

    def test_patterns_ribs(self) -> None:
        self.plotmaker.get_ribs()
        dwg = Layout.stack_row(self.plotmaker.ribs, 0.1)
        dwg.export_dxf(os.path.join(TEMPDIR, "test_ribs.dxf"))

if __name__ == "__main__":
    unittest.main()