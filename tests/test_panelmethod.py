import unittest

from openglider.physics.flow import GliderPanelMethod

from common import TestCase


class PanelMethodTest(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()
        self.glider3d = self.glider2d.get_glider_3d()
        self.glidercase = GliderPanelMethod(self.glider3d, {"v_inf": [10,0,2]})

    def test_run(self):
        self.glidercase.run()


if __name__ == "__main__":
    unittest.main()

