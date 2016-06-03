import unittest

from openglider.physics.mech import GliderFemCase

from common import TestCase


class PanelMethodTest(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()
        self.glider3d = self.glider2d.get_glider_3d()
        self.glidercase = GliderFemCase(self.glider3d)

    def test_run(self):
    	self.glidercase.fix_attachment_points()


if __name__ == "__main__":
    unittest.main()

