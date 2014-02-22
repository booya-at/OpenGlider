import random
import sys
import os

from visual_test_glider import GliderTestClass

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.glider.cell_elements import DiagonalRib, Panel
import openglider.graphics as Graph


class TestCellElements(GliderTestClass):
    def setUp(self, complete=True):
        super(TestCellElements, self).setUp()
        self.cell_no = random.randint(0, len(self.glider.cells) - 1)
        self.cell = self.glider.cells[self.cell_no]

    def test_diagonal_rib_3d(self):
        cell = self.glider.cells[self.cell_no]
        diag = DiagonalRib((0.1, -1), (0.3, -1), (0.1, 0.8), (0.5, 0.8), self.cell_no)
        l1, l2 = diag.get_3d(self.glider)
        l1 = l1.tolist()
        Graph.Graphics([Graph.Line(cell.rib1.profile_3d.data),
                        Graph.Line(cell.rib2.profile_3d.data),
                        Graph.Polygon(l1 + l2[::-1])])

    def test_diagonal_rib_2d(self):
        diag = DiagonalRib((0.1, -1), (0.3, -1), (0.1, 0.8), (0.5, 0.8), self.cell_no)
        l1, l2 = diag.get_flattened(self.glider, ribs_flattened=None)
        Graph.Graphics2D([Graph.Line(l1.data.tolist()+l2.data.tolist()[::-1])])

    def test_panel_3d(self):
        l1, r1, l2, r2 = sorted([random.random() for __ in range(4)])
        panel = Panel(l1, l2, r1, r2, self.cell_no)
        ribs = panel.get_3d(glider=self.glider, numribs=10)
        Graph.Graphics(map(Graph.Line, ribs))

    def test_panel_2d(self):
        # TODO: !
        pass