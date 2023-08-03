import unittest
import random

import euklid

import openglider
from openglider.glider.rib.rib import Rib
from openglider.glider.rib.crossports import RibHole
from openglider.materials import cloth
from openglider.vector.unit import Percentage

class TestRib(unittest.TestCase):

    def setUp(self) -> None:
        naca = random.randint(1, 99) * 100 + random.randint(1, 99) # camber / thickness (thickness > 0)
        numpoints = random.randint(10,11)
        self.prof = openglider.airfoil.Profile2D.compute_naca(naca, numpoints)
        self.rib = Rib(profile_2d=self.prof,
                       pos=euklid.vector.Vector3D([random.random(), random.random(), random.random()]),
                       chord=random.random(),
                       arcang=random.random(),
                       aoa_absolute=random.random(),
                       glide=random.random()*10,
                       material=cloth.get("default"))

    #def test_normvectors(self) -> None:

    def test_align(self) -> None:
        first = self.rib.pos
        second = self.rib.align(euklid.vector.Vector2D([0, 0]))
        for i in range(3):
            self.assertAlmostEqual(first[i], second[i])

    def test_align_scale(self) -> None:
        prof1 = [self.rib.align(p) for p in self.rib.profile_2d.curve]
        _prof2 = self.rib.profile_2d.curve.scale(self.rib.chord)
        prof2 = [self.rib.align(p, scale=False) for p in _prof2]


        for p1, p2 in zip(prof1, prof2):
            self.assertAlmostEqual(p1[0], p2[0])
            self.assertAlmostEqual(p1[1], p2[1])
            self.assertAlmostEqual(p1[2], p2[2])

    def test_mesh(self) -> None:
        self.rib.holes.append(RibHole(pos=Percentage(0.2)))
        self.rib.get_mesh()




if __name__ == '__main__':
    unittest.main(verbosity=2)
