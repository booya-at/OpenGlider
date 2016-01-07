import unittest

from common import *
from openglider import jsonify
from openglider.glider import ParametricGlider


class GliderTestCase2D(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()

    def test_fit(self):
        glider_3d = self.import_glider()
        self.assertEqualGlider2D(ParametricGlider.fit_glider_3d(glider_3d), self.glider2d)

    def test_create_glider(self):
        glider = self.glider2d.get_glider_3d()
        self.assertAlmostEqual(glider.span, 2*self.glider2d.shape.span, 2)

    def test_export(self):
        exp = jsonify.dumps(self.glider2d)
        imp = jsonify.loads(exp)['data']
        self.assertEqualGlider2D(self.glider2d, imp)

    def test_export_ods(self):
        exp = self.glider2d.export_ods("/tmp/test.ods")

    def test_set_area(self):
        self.glider2d.set_flat_area(10)
        self.assertAlmostEqual(self.glider2d.flat_area, 10)

if __name__ == '__main__':
    unittest.main(verbosity=2)