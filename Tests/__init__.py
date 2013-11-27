#!/bin/python2
__author__ = 'simon'
import random
import unittest
from openglider.Profile import Profile2D, Profile3D
from openglider.Cells import BasicCell
from openglider.Ribs import Rib
import numpy
from openglider.Vector import Vectorlist2D

class TestProfile(unittest.TestCase):

    def setUp(self):
        self.prof=Profile2D()
        self.prof.importdat("/home/simon/test.dat")

    def test_numpoints(self):
        num=random.randint(4,500)
        self.prof.Numpoints=num
        self.assertEqual(num+1- num % 2, self.prof.Numpoints)

    def test_profilepoint(self):
        x=random.random()*random.randint(-1,1)
        self.assertEqual(abs(x),self.prof.profilepoint(x)[1][0])


class TestVectorList(unittest.TestCase, Vectorlist2D):
    def setUp(self):
        i=1
        self.data=[[0.,0.]]
        while i<20:
            self.data+=[[self.data[-1][0]+random.random(), self.data[-1][1]+random.random()]]
            i+=1
        self.data=numpy.array(self.data)
        self.check()

    def testCut(self):
        i=random.randint(0,len(self.data)-2)
        k=random.random()
        dirr=[random.randint(0,40),random.randint(0,40)]

        p1=self.point(i,k)+dirr
        p2=self.point(i,k)-dirr
        neu=self.cut(p1,p2,i)
        self.assertEqual(i,neu[1][0])
        self.assertAlmostEquals(k,neu[1][1])

    def testExtend(self):
        i = random.randint(0,len(self.data)-2)
        k = random.random()
        leng = random.random()*random.randint(-10,10)
        (i2,k2)=self.extend((i,k),leng)
        if i<i2 or (i==i2 and k<k2):
            leng2=self.get_length((i,k),(i2,k2))
        else:
            leng2=self.get_length((i2,k2),(i,k))
        self.assertAlmostEquals(leng2, abs(leng))


#class TestBezierCurve(object):
#    def setUp(self):


if __name__ == '__main__':
        unittest.main(verbosity=2)
