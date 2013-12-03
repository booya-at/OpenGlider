#!/bin/python2
__author__ = 'simon'
import random
import unittest
from openglider.Profile import Profile2D, Profile3D
from openglider.Cells import BasicCell
from openglider.Ribs import Rib
import numpy
from openglider.Vector import Vectorlist2D
from openglider import Vector

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
        (i2,k2) = self.extend_old((i,k),leng)
        if i<i2 or (i==i2 and k<k2):
            leng2=self.get_length_old((i,k),(i2,k2))
        else:
            leng2=self.get_length_old((i2,k2),(i,k))
        self.assertAlmostEquals(leng2, abs(leng))


#class TestBezierCurve(object):
#    def setUp(self):
class newStuffTest(unittest.TestCase):

    def setUp(self):
        self.vectors = []
        for i in range(10):
            #make the points
            pointlist = []
            for u in range(100):
                pointlist.append([random.choice(range(0, 200)) / 10., random.choice(range(0, 200)) / 10.])  # ? ??
            self.vectors.append(Vector.Vectorlist(pointlist))
        self.ius = []
        for nix in range(10):
            #make the iu's
            iu = random.random()*200 - 50

            if iu < 0:
                u = iu
                i = 0
            else:
                i = min(int(iu), 100-2)  # Upper Limit for i
                # case1: 0<ik<len -> k=ik%1;
                # case2: ik>len(self.data) -> k += difference
                u = iu % 1 + max(0, int(iu) - 100+2)
            self.ius.append([i, u, iu])

    def test_my_extract_function(self):
        for i, u, iu in self.ius:
            extend_value = random.choice(range(-1000, 2000)) / 10.
            for vectorlist in self.vectors:
                value2_list = vectorlist.extend_old([i, u], extend_value)
                value = vectorlist.extend(iu, extend_value)
                value2 = value2_list[0] + value2_list[1]
                print(str(value), str(value2))
                self.assertAlmostEqual(value, value2)

    def test_my_getlength_function(self):
        for i, u, iu in self.ius:
            for vectorlist in self.vectors:
                for i2, u2, iu2 in self.ius:
                    self.assertAlmostEqual(vectorlist.get_length_old([i, u], [i2, u2]), vectorlist.get_length(iu, iu2))

if __name__ == '__main__':
        unittest.main(verbosity=2)
