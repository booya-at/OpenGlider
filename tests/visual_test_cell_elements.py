import random
import sys
import os

from visual_test_glider import GliderTestClass

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.glider.cell_elements import DiagonalRib
import openglider.Graphics as Graph


class TestCellElements(GliderTestClass):
    def test_diagonal_rib_3d(self):
        cell_no = random.randint(0, len(self.glider.cells) - 1)
        diag = DiagonalRib((0.1, -1), (0.3, -1), (0.1, 0.8), (0.5, 0.8), cell_no)
        l1, l2 = diag.get_3d(self.glider)
        l1 = l1.tolist()
        cell = self.glider.cells[cell_no]
        Graph.Graphics([Graph.Line(cell.rib1.profile_3d.data),
                        Graph.Line(cell.rib2.profile_3d.data),
                        Graph.Polygon(l1 + l2[::-1])])