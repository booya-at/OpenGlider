__author__ = 'simon'
import unittest
import random

from .. import Vector

class JonaTest(unittest.TestCase):

    def setUp(self):
        self.vectors = []
        for i in range(100):
            #make the points
            pointlist = []
            for u in range(100):
                pointlist.append([random.choice(range(0, 200)) / 10., random.choice(range(0, 200)) / 10.])  # ? ??
            self.vectors.append(Vector.Vectorlist(pointlist))

    def test_my_extract_function(self):
        for i in range(100):
            i = random.choice(range(0, 99))
            u = random.choice(range(-1000, 2000)) / 10.
            iu = i + u
            print("i: %s, u: %s, ui: %s" % (i,u,iu))
            extend_value = random.choice(range(-1000, 2000)) / 10.
            for vectorlist in self.vectors:
                point1 = vectorlist.extend_old([i, u], extend_value)
                point2 = vectorlist.extend(iu, extend_value)
                print(str(point1))
                self.assertEqual(point1.x, point2.x)
