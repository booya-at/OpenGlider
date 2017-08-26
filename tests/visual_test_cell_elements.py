import random
import sys
import os
import unittest

from visual_test_glider import GliderTestClass

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
from openglider.glider.cell import DiagonalRib, Panel, TensionStrap
import openglider.graphics as Graph


class TestCellElements(GliderTestClass):
    def setUp(self, complete=True):
        super(TestCellElements, self).setUp()
        self.cell_no = random.randint(0, len(self.glider.cells) - 1)
        self.cell = self.glider.cells[self.cell_no]

    def test_diagonal_rib_3d(self):
        cell = self.glider.cells[self.cell_no]
        diag = DiagonalRib((0.1, -1), (0.3, -1), (0.1, 0.8), (0.5, 0.8))
        l1, l2 = diag.get_3d(cell)
        l1 = l1.data.tolist()
        Graph.Graphics([Graph.Line(cell.rib1.profile_3d.data),
                        Graph.Line(cell.rib2.profile_3d.data),
                        Graph.Polygon(l1 + l2[::-1])])

    def test_diagonal_rib_2d(self):
        diag = DiagonalRib((0.1, -1), (0.3, -1), (0.1, 0.8), (0.5, 0.8))
        l1, l2 = diag.get_flattened(self.cell, ribs_flattened=None)
        Graph.Graphics2D([Graph.Line(l1.data.tolist()+l2.data.tolist()[::-1])])

    def get_diagonal(self, x):
        diag = DiagonalRib((x-0.01, -1), (x+0.01, -1), (x-0.06, 1), (x+0.06, 1))
        l1, l2 = diag.get_3d(self.cell)
        l1 = l1.data.tolist()
        l2 = l2.data.tolist()
        return Graph.Polygon(l1 + l2[::-1], colour=Graph.Red)

    def get_strap(self, x):
        strap = TensionStrap(x, x, 0.02)
        l1, l2 = strap.get_3d(self.cell)
        l1 = l1.data.tolist()
        l2 = l2.data.tolist()
        return Graph.Polygon(l1 + l2[::-1], colour=Graph.Green)



    def get_panels(self):
        dc = ["left", "right", "type"]
        panel1 = Panel(dict(zip(dc, [-1, -1, 2])), dict(zip(dc, [0.01, 0.01, 2])))
        panel2 = Panel(dict(zip(dc, [.06, .06, 2])), dict(zip(dc, [1, 1, 2])))
        ribs = panel1.get_3d(self.cell, numribs=10)

        mesh = (panel1.get_mesh(self.cell, numribs=9) +
                panel2.get_mesh(self.cell, numribs=9))
        tris = mesh.all_polygons
        return [Graph.Polygon(tri) for tri in tris]

    def test_panel_3d(self):
        Graph.Graphics(self.get_panels())

    def test_all(self):
        att = (0.1, 0.3, 0.55, 0.8)
        panels = self.get_panels()
        diagonals = [self.get_diagonal(x) for x in att]
        straps = [self.get_strap(x) for x in att]

        Graph.Graphics([Graph.Line(self.cell.rib1.profile_3d.data),
                        Graph.Line(self.cell.rib2.profile_3d.data)] + panels + diagonals + straps)

    def test_panel_2d(self):
        # TODO: !
        pass

if __name__ == "__main__":
    unittest.main()