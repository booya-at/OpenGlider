import unittest

from openglider.physics.mech import GliderFemCase
from openglider.utils.distribution import Distribution
from openglider.utils import Config
from openglider import load

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
            "fem_steps": 200000,
            "fem_output": 100,
            "d_velocity": 1.,
            "pressure_ramp": 100,     # steps for linear pressure ramp
            "caseType": "line_forces",
            "line_numpoints": 10,
            "line_rho": 0.00001,
            "line_elasticity": 30000,
            "rib_rho": 0.00001,
            "cell_numpoints": 0,
            "vtk_fem_output": "/tmp/Fem/testFEM",
            "symmetric_case": True,
            "line_numpoints": 2,
            "distribution": Distribution.from_nose_cos_distribution(30, 0.3)
        }

        self.glidercase = GliderFemCase(self.glider3d, config)
        self.glidercase.run()


if __name__ == "__main__":
    unittest.main()
