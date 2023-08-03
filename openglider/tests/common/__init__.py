import sys
import os
import unittest

from openglider.glider.project import GliderProject

try:
    import openglider
except ImportError:
    def stepup(path: str | os.PathLike, num: int) -> str | os.PathLike:
        if num == 0:
            return path
        else:
            return stepup(os.path.dirname(path), num-1)
    
    sys.path.append(str(stepup(__file__,3)))
    import openglider

import openglider.glider
from openglider.glider import Glider
from openglider.glider.parametric import ParametricGlider

import_dir = os.path.dirname(os.path.abspath(__file__))
test_dir = os.path.dirname(import_dir)
demokite = import_dir + '/demokite.ods'
#demokite = import_dir + "/demokite.json"


class GliderTestCase(unittest.TestCase):
    project: GliderProject

    def setUp(self) -> None:
        self.project = openglider.load(demokite)

    @property
    def parametric_glider(self) -> ParametricGlider:
        return self.project.glider
    
    @property
    def glider(self) -> Glider:
        return self.project.glider_3d

    def assertEqualGlider(self, glider1: Glider, glider2: Glider, precision: int=None) -> None:
        self.assertEqual(len(glider1.ribs), len(glider2.ribs))
        self.assertEqual(len(glider1.cells), len(glider2.cells))
        for rib_no, (rib_1, rib_2) in enumerate(zip(glider1.ribs, glider2.ribs)):
            # test profile_3d this should include align, profile,...
            for xyz_1, xyz_2 in zip(rib_1.profile_3d.curve.nodes, rib_2.profile_3d.curve.nodes):
                for i, (_p1, _p2) in enumerate(zip(xyz_1, xyz_2)):
                    self.assertAlmostEqual(_p1, _p2, places=precision, msg=f"Not matching at Rib {rib_no}, Coordinate {i}; {_p1}//{_p2}")
                    # todo: expand test: lines, diagonals,...

    def assertEqualGlider2D(self, glider1: ParametricGlider, glider2: ParametricGlider) -> None:
        self.assertEqual(glider1.shape.cell_num, glider2.shape.cell_num)

if __name__ == "__main__":
    dirname = os.path.dirname(__file__)
    glider = ParametricGlider.import_ods(os.path.join(dirname, "demokite.ods"))
    with open(demokite, "w") as outfile:
        openglider.jsonify.dump(glider, outfile)