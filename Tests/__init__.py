#!/bin/python2
__author__ = 'simon'
import unittest
from openglider.Profile import Profile2D
from openglider.Tests.test_vectorlist import *
import os.path

testfolder = os.path.dirname(os.path.abspath( __file__ ))

class TestProfile(unittest.TestCase):
    def setUp(self):
        self.prof = Profile2D()
        self.prof.importdat(testfolder+"/testprofile.dat")

    def test_numpoints(self):
        num = random.randint(4, 500)
        self.prof.Numpoints = num
        self.assertEqual(num + 1 - num % 2, self.prof.Numpoints)

    def test_profilepoint(self):
        x = random.random()*random.randint(-1, 1)
        self.assertEqual(abs(x), self.prof.profilepoint(x)[1][0])



if __name__ == '__main__':
        unittest.main(verbosity=2)
