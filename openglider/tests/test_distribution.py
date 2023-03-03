import random
from typing import Any
import unittest

import numpy as np

from openglider.utils.distribution import Distribution


class TestProfile(unittest.TestCase):
    num_dist = 41
    num_fixed = 10

    def setUp(self) -> None:
        self.fixpoints = [(random.random()-0.5)*2 for _ in range(self.num_fixed)]

        self.dist_types = "cos, cos_2, nose_cos, const"
    
    def _get_kwargs(self) -> dict[str, Any]:
        return {
            "numpoints": self.num_dist,
        }
    
    def _test_dist(self, dist: Distribution) -> None:
        self.assertEqual(len(dist), self.num_dist)

    def test_cos(self) -> None:
        dist = Distribution.from_cos_distribution(self.num_dist)
        self._test_dist(dist)

    def test_cos2(self) -> None:
        dist = Distribution.from_cos_2_distribution(self.num_dist)
        self._test_dist(dist)

    def test_nose_cos(self) -> None:
        dist = Distribution.from_nose_cos_distribution(self.num_dist)
        self._test_dist(dist)

    def test_linear(self) -> None:
        dist = Distribution.from_linear(self.num_dist)
        self._test_dist(dist)



if __name__ == '__main__':
    unittest.main(verbosity=2)
