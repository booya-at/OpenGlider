import unittest

from openglider.physics.mech import GliderFemCase

from common import TestCase


class FemTest(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()
        self.glider3d = self.glider2d.get_glider_3d()
        self.glidercase = GliderFemCase(self.glider3d)

    def test_run(self):
        self.glidercase.fix_attachment_points()
        self.glidercase.config.v_inf = [10, 0, 1]
        self.glidercase.run()


if __name__ == "__main__":
    unittest.main()

