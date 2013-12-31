__author__ = 'simon'
import unittest
from openglider.Utils import Ballooning
import random


class TestBallooningBezier(unittest.TestCase):
    def setUp(self):
        self.ballooning = Ballooning.BallooningBezier()

    def test_multiplication(self):
        for i in range(100):
            factor = random.random()
            temp = self.ballooning * factor
            val = random.random()
            self.assertAlmostEqual(temp[val], self.ballooning[val] * factor)

    def test_addition(self):
        for i in range(100):
            val = random.random()
            self.assertAlmostEqual(2 * self.ballooning[val], (self.ballooning + self.ballooning)[val])


if __name__ == '__main__':
    unittest.main(verbosity=2)