import unittest
from openglider.tests.common import GliderTestCase


class GliderTestCase2D(GliderTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.shape = self.parametric_glider.shape.get_half_shape()

    def test_chords(self) -> None:
        shape = self.shape
        # print(shape)

if __name__ == '__main__':
    unittest.main()