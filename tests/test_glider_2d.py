import unittest

from common import *
from openglider import jsonify
from openglider.glider.glider_2d import Glider2D


class GliderTestCase2D(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()

    def test_fit(self):
        glider_3d = self.import_glider()
        self.assertEqualGlider2D(Glider2D.fit_glider_3d(glider_3d), self.glider2d)

    def test_create_glider(self):
        glider = self.glider2d.get_glider_3d()
        self.assertAlmostEqual(glider.span, self.glider2d.span, 3)

    def test_export(self):
        exp = jsonify.dumps(self.glider2d)
        imp = jsonify.loads(exp)['data']
        self.assertEqualGlider2D(self.glider2d, imp)

if __name__ == '__main__':
    unittest.main()