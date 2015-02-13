from common import *


from visual_test_glider import TestGlider

__ALL__ = ['GliderTestCase2D']


class GliderTestCase2D(TestCase):
    def setUp(self):
        self.glider = self.import_glider()
        self.glider2d_ = Glider2D.fit_glider_3d(self.glider)
        self.glider2d = self.import_glider_2d()
        #self.glider = self.glider2d.get_glider_3d()

    def test_fit(self):
        self.assertEqualGlider(self.glider, self.glider2d.get_glider_3d(), precision=1)

    def test_show_glider(self):
        print(self.glider2d.cell_num)
        self.glider2d.cell_num += 15
        glider3d = self.glider2d.get_glider_3d()
        TestGlider.show_glider(glider3d)