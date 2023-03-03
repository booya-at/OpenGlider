import unittest
import random

from openglider.tests.common import openglider
from openglider.glider import ballooning
import euklid

class TestBallooningBezier(unittest.TestCase):
    @classmethod
    def get_ballooning(cls) -> ballooning.BallooningBezier:
        num = random.randint(10, 30)
        x_values = [i/(num-1) for i in range(num)]
        upper = [euklid.vector.Vector2D([x, random.random()*0.1]) for x in x_values]
        lower = [euklid.vector.Vector2D([x, random.random()*0.1]) for x in x_values]
        return ballooning.BallooningBezier(upper, lower)

    def setUp(self) -> None:
        self.ballooning = self.get_ballooning()

    def test_multiplication(self) -> None:
        for i in range(100):
            factor = random.random()
            temp = self.ballooning * factor
            val = random.random()
            self.assertAlmostEqual(temp[val], self.ballooning[val] * factor)

    def test_addition(self) -> None:
        num = 100
        x_values = [(i-num)/num for i in range(2*num+1)]
        b1 = self.get_ballooning()
        b2 = self.get_ballooning()
        mixed = b1 + b2
        for x in x_values:
            self.assertAlmostEqual(b1[x]+b2[x], mixed[x], places=2)


if __name__ == '__main__':
    unittest.main(verbosity=2)