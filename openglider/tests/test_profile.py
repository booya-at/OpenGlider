import os
import tempfile
import unittest
import random

from openglider.tests.common import import_dir
from openglider.airfoil import Profile2D

TEMPDIR =  tempfile.gettempdir()

class TestProfile(unittest.TestCase):
    def setUp(self) -> None:
        self.prof = Profile2D.import_from_dat(import_dir + "/testprofile.dat").normalized()

    def test_numpoints(self) -> None:
        num = random.randint(4, 500)

        prof2 = self.prof.resample(num)

        self.assertEqual(num + 1 - num % 2, prof2.numpoints)

    def test_export(self) -> None:
        path = os.path.join(TEMPDIR, "prof.dat")
        self.prof.export_dat(path)

    def test_profilepoint(self) -> None:
        x = random.random() * random.randint(-1, 1)
        self.assertAlmostEqual(abs(x), self.prof.profilepoint(x)[0])

    def test_multiplication(self) -> None:
        factor = random.random()
        other = self.prof * factor
        self.assertAlmostEqual(other.thickness, self.prof.thickness * factor)
        other *= 1. / factor
        self.assertAlmostEqual(other.thickness, self.prof.thickness)

    @unittest.skip("skip")
    def test_area(self) -> None:
        factor = random.random()
        self.assertAlmostEqual(factor * self.prof.curve.get_area(), (self.prof * factor).curve.get_area())

    def test_compute_naca(self) -> None:
        numpoints = random.randint(10, 200)
        thickness = random.randint(8, 20)
        m = random.randint(1, 9) * 1000  # Maximum camber position
        p = random.randint(1, 9) * 100  # Maximum thickness position
        prof = Profile2D.compute_naca(naca=m+p+thickness, numpoints=numpoints)
        self.assertAlmostEqual(prof.thickness*100, thickness, 0)

    def test_add(self) -> None:
        other = self.prof.copy()
        other = self.prof + other
        self.assertAlmostEqual(2*self.prof.thickness, other.thickness)

    def test_mul(self) -> None:
        self.prof *= 0

    def test_thickness(self) -> None:
        val = random.random()
        thickness = self.prof.thickness

        new = self.prof.set_thickness(thickness*val)

        self.assertAlmostEqual(new.thickness, thickness*val)

    @unittest.skip("whatsoever!")
    def test_camber(self) -> None:
        val = random.random()
        camber = max(self.prof.camber[:, 1])

        new = self.prof.set_camber(camber*val)

        self.assertAlmostEqual(new.camber, camber*val)

    def test_contains_point(self) -> None:
        allowance = random.random()*0.1
        prof_big = self.prof.copy()
        
        prof_big.curve = prof_big.curve.offset(2*allowance).close()
        
        for p in self.prof.curve:
            self.assertTrue(prof_big.curve.contains(p))
        for p in prof_big.curve:
            self.assertFalse(self.prof.curve.contains(p))


if __name__ == '__main__':
    unittest.main(verbosity=2)
