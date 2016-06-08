import unittest

from openglider import jsonify


class PlotTestCase(unittest.TestCase):
    def setUp(self):
        self.glider_2d = jsonify.load("../common/glider2d.json")
        self.glider_3d = self.glider_2d.get_glider_3d()