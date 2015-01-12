import sys
import os
import unittest

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider

import openglider.glider
from openglider.glider.glider_2d import Glider2D

import_dir = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.dirname(import_dir)
demokite = import_dir + '/demokite.ods'


class TestCase(unittest.TestCase):
    @classmethod
    def import_glider(cls):
        return openglider.glider.Glider.import_geometry(path=demokite)

    def assertEqualGlider(self, glider1, glider2, precision=None):
        self.assertEqual(len(glider1.ribs), len(glider2.ribs))
        self.assertEqual(len(glider1.cells), len(glider2.cells))
        for rib_no, (rib_1, rib_2) in enumerate(zip(glider1.ribs, glider2.ribs)):
            # test profile_3d this should include align, profile,...
            for xyz_1, xyz_2 in zip(rib_1.profile_3d, rib_2.profile_3d):
                for i, (_p1, _p2) in enumerate(zip(xyz_1, xyz_2)):
                    self.assertAlmostEqual(_p1, _p2, places=precision, msg="Not matching at Rib {}, Coordinate {}; {}//{}".format(rib_no, i, _p1, _p2))
                    # todo: expand test: lines, diagonals,...

    def assertEqualGlider2D(self, glider1, glider2):
        self.assertEqual(glider1.cell_num, glider2.cell_num)