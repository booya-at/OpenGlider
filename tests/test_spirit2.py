"""Spirit 2 (ASA, size 28.6 m2): an older wing, out of production, of which more than 100 were sewn in several sizes.

Built in OpenGlider from the original Matlab design; the cutting patterns match the Matlab ones (cells 3-29 to
0.01 mm, the center cell within 1 mm). Main lines A, B, C, D and the brake cascade of the line plan. Inner structure
from the Matlab data: diagonal ribs in three rows (A, B, C) next to the loaded ribs, elliptic holes in the ribs;
trailing edge miniribs in all cells but the five of the wing tip. Some diagonals may be missing: part of the original
design data was lost over the years.

Added from the FEM / CFD study of the wing (2026-11): straps of rows A, B and C on the lower surface (one per cell,
own width on each rib) and a nose 3D cut on the upper side of cells 1-21 (7 % and 18.5 % of the chord, sagitta 4 and
2 mm in the widest cell) given by its designed sagitta.
"""
import os
import unittest

import openglider
from openglider.plots import PlotMaker

spirit2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "common", "spirit2.json")


class TestSpirit2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.glider_2d = openglider.load(spirit2)
        cls.glider = cls.glider_2d.get_glider_3d()

    def test_geometry(self):
        self.assertEqual(len(self.glider.ribs), 29)
        self.assertEqual(len(self.glider.cells), 28)
        self.assertAlmostEqual(self.glider.area, 28.56, delta=0.05)

    def test_lines(self):
        self.assertEqual(len(self.glider.lineset.lines), 75)
        self.assertEqual(len([line for line in self.glider.lineset.lines if line.name.startswith("brake")]), 21)

    def test_straps(self):
        self.assertEqual(sum(len(cell.straps) for cell in self.glider.cells), 45)
        for cell in self.glider.cells:
            for strap in cell.straps:  # on the lower side, 100 .. 150 mm wide on both ribs
                self.assertEqual(strap.left_front[1], -1)
                self.assertTrue(0.098 < strap.width_left * cell.rib1.chord < 0.152)
                self.assertTrue(0.098 < strap.width_right * cell.rib2.chord < 0.152)

    def test_cut_3d(self):
        cell = self.glider.cells[5]
        self.assertEqual(len(cell.panels), 3)
        cell.calculate_3d_shaping(numribs=10)
        cut = next(p.cut_back for p in cell.panels if p.cut_back["type"] == "cut_3d" and abs(p.cut_back["left"] + 0.07) < 1e-9)
        amount = cut["amount_3d"]
        self.assertEqual(len(amount), 12)
        self.assertAlmostEqual(amount[0], 0)
        self.assertAlmostEqual(max(amount), cut["sagitta"], delta=0.02 * cut["sagitta"])
        self.assertTrue(0.003 < cut["sagitta"] < 0.0041)

    def test_diagonals(self):
        self.assertEqual(sum(len(cell.diagonals) for cell in self.glider.cells), 44)

    def test_holes(self):
        # 4 holes in the loaded ribs, 6 in the others, none in the tip rib (rib 0 is the mirror of rib 1)
        self.assertEqual(sum(len(rib.holes) for rib in self.glider.ribs[1:]), 144)
        rib = self.glider.ribs[1]
        profile = rib.profile_2d
        for hole in rib.holes:
            for x, y in hole.get_points(rib).data:  # inside the profile
                self.assertLess(profile[profile(x)][1], y)
                self.assertLess(y, profile[profile(-x)][1])

    def test_miniribs(self):
        self.assertEqual(sum(len(cell.miniribs) for cell in self.glider.cells), 23)
        self.assertEqual(sum(len(cell.miniribs) for cell in self.glider.cells[-5:]), 0)

    def test_panels(self):
        plotmaker = PlotMaker(self.glider)
        for cell in self.glider.cells:
            cpm = plotmaker._get_cellplotmaker(cell)
            parts = cpm.get_panels_upper() + cpm.get_panels_lower()
            self.assertEqual(len(parts), len(cell.panels))


if __name__ == "__main__":
    unittest.main()
