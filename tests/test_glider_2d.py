import unittest


from common import *
from openglider import jsonify
from openglider.glider import Glider2D


class GliderTestCase2D(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()

    def test_fit(self):
        glider_3d = self.import_glider()
        self.assertEqualGlider(glider_3d, self.glider2d.get_glider_3d(), precision=0)

    #@unittest.skip('')
    def test_create_glider(self):
        glider = self.glider2d.get_glider_3d()

    def test_export(self):
        exp = jsonify.dumps(self.glider2d)
        imp = jsonify.loads(exp)['data']
        self.assertEqualGlider2D(self.glider2d, imp)