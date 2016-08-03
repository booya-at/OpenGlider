import unittest

from openglider.physics.flow import GliderPanelMethod
from openglider.utils.distribution import Distribution

from common import TestCase


class PanelMethodTest(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()
        self.glider3d = self.glider2d.get_glider_3d()
        config = {"v_inf": [10,0,2],
                  "symmetric_case": True,
                  "cell_numpoints": 2,
                  "distribution": Distribution.from_nose_cos_distribution(60, 0.2)
                  }
        self.glidercase = GliderPanelMethod(self.glider3d, config)

    def test_run(self):
        self.glidercase.run()
        self.glidercase.export_vtk("/tmp/glider.vtk")


if __name__ == "__main__":
    unittest.main()

