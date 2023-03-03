import random
import unittest

from openglider.tests.common import *


class TestGlider(GliderTestCase):
    #def __init__(self):
    #    unittest.TestCase.__init__(self)

    def test_numpoints(self) -> None:
        numpoints = random.randint(1, 100)*2+1
        self.glider.profile_numpoints = numpoints
        self.assertEqual(self.glider.profile_numpoints, numpoints)

    def test_span(self) -> None:
        span = random.random() * 100
        self.glider.span = span
        self.assertAlmostEqual(self.glider.span, span)

    def test_area(self) -> None:
        area = random.random() * 100
        self.glider.area = area
        self.assertAlmostEqual(self.glider.area, area)

    def test_aspectratio(self) -> None:
        ar = random.randint(4, 15) + random.random()
        area_bak = self.glider.area
        for i in range(15):
            self.glider.aspect_ratio = ar  # -> Do some times and its precise
        self.assertAlmostEqual(area_bak, self.glider.area)
        self.assertAlmostEqual(ar, self.glider.aspect_ratio, 3)

    def test_scale(self) -> None:
        ar = self.glider.aspect_ratio
        self.glider.scale(1+random.random())
        self.assertAlmostEqual(ar, self.glider.aspect_ratio)

    def test_flatten(self) -> None:
        y = random.random()*len(self.glider.cells)
        self.glider.get_midrib(y).flatten()

    def copy_complete(self) -> None:
        self.glider.copy_complete()

    def test_mean_rib(self) -> None:
        for cell in self.glider.cells:
            cell.mean_airfoil(10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
