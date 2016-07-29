import unittest

from openglider.physics.mech import GliderFemCase
from openglider.utils.distribution import Distribution
from openglider.utils import Config

from common import TestCase


class FemTest(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()
        self.glider2d.lineset.lines = [line for line in self.glider2d.lineset.lines if line.layer != "brake"]

        self.glider3d = self.glider2d.get_glider_3d()

    def test_run(self):
        config = {
            "v_inf": [14, 0, 2],
            "fem_timestep": 1.e-06,
            "fem_steps": 100000,
            "fem_output": 300,
            "d_velocity": 1.5,
            "pressure_ramp": 100,     # steps for linear pressure ramp
            "caseType": "full",
            "line_numpoints": 10,
            "line_rho": 0.00001,
            "cell_numpoints": 4,
            "distribution": Distribution.from_nose_cos_distribution(60)
        }

        self.glidercase = GliderFemCase(self.glider3d, config)
        self.glidercase.run()


if __name__ == "__main__":
    unittest.main()
