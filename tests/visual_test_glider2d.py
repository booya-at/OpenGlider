from common import *


from visual_test_glider import TestGlider

__ALL__ = ['GliderTestCase2D']


class GliderTestCase2D(TestCase):
    def setUp(self):
        self.glider2d = Glider2D()

    def test_fit(self):
        glider = self.import_glider()
        self.glider2d = Glider2D.fit_glider(glider)
        self.assertEqualGlider(glider, self.glider2d.glider_3d(), precision=1)

    def test_show_glider(self):
        glider = self.import_glider()
        glider2d = Glider2D.fit_glider(glider)
        TestGlider.show_glider(glider)
        TestGlider.show_glider(glider2d.glider_3d())