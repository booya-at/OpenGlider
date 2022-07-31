import unittest
from .common import TestCase


class GliderTestCase2D(TestCase):
    def setUp(self):
        self.glider2d = self.import_glider_2d()
        self.shape = self.glider2d.shape.get_half_shape()

    def test_chords(self):
        shape = self.shape
        # print(shape)

if __name__ == '__main__':
    unittest.main()