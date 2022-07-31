import unittest
import random

import openglider
from openglider.glider.rib.rib import Rib
from openglider.glider.rib.crossports import RibHole
from openglider.mesh import Mesh


class TestRib(unittest.TestCase):

    def setUp(self):
        naca = random.randint(1, 99) * 100 + random.randint(1, 99) # camber / thickness (thickness > 0)
        numpoints = random.randint(10,11)
        self.prof = openglider.airfoil.Profile2D.compute_naca(naca, numpoints)
        self.rib = Rib(self.prof,
                       startpoint=[random.random(), random.random(), random.random()],
                       chord=random.random(),
                       arcang=random.random(),
                       aoa_absolute=random.random(),
                       glide=random.random()*10)


    def test_normvectors(self):
        normvectors = self.rib.normvectors

    def test_align(self):
        first = self.rib.pos
        second = self.rib.align([0, 0, 0])
        for i in range(3):
            self.assertAlmostEqual(first[i], second[i])

    def test_align_scale(self):
        prof1 = [self.rib.align(list(p)) for p in self.rib.profile_2d.curve]
        _prof2 = self.rib.profile_2d.curve.scale(self.rib.chord)
        prof2 = [self.rib.align(list(p), scale=False) for p in _prof2]


        for p1, p2 in zip(prof1, prof2):
            self.assertAlmostEqual(p1[0], p2[0])
            self.assertAlmostEqual(p1[1], p2[1])
            self.assertAlmostEqual(p1[2], p2[2])

    def test_mesh(self):
        self.rib.holes.append(RibHole(0.2))
        self.rib.get_mesh()




if __name__ == '__main__':
    unittest.main(verbosity=2)
