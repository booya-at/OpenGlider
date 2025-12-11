
import sys
import os
import unittest
import random
import numpy as np

try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
    import openglider
import openglider.graphics
import openglider.plots.marks as marks


class TestMarks(unittest.TestCase):
    def setUp(self):
        self.p1 = np.array([0, 0])
        self.p2 = np.array([random.random(), random.random()])

    def show(self, obj):
        openglider.graphics.Graphics2D([
            openglider.graphics.Point([self.p1, self.p2]),
            openglider.graphics.Polygon(obj[0])
        ])

    def test_triangle(self):
        self.show(marks.triangle(self.p1, self.p2))

    def test_square(self):
        self.show(marks.polygon(self.p1, self.p2, num=4))

    def test_circle(self):
        self.show(marks.polygon(self.p1, self.p2, num=20))