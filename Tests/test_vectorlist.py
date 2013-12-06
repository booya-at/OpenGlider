__author__ = 'simon'
import unittest
import random
from openglider import Vector


class TestVector3D(unittest.TestCase):
    def setUp(self, dim=3):
        self.vectors = []
        self.sums = []
        numlists = 100
        self.numpoints = numpoints = 100
        for i in range(numlists):
            #make the points
            pointlist = []
            for u in range(numpoints):
                pointlist.append([random.random()*100 for i in range(dim)])
            self.vectors.append(Vector.Vectorlist(pointlist))

    def test_extend_total(self):
        """Sum up the length of the list and check"""
        for thalist in self.vectors:
            total = 0
            for i in range(self.numpoints-1):
                total += Vector.norm(thalist[i]-thalist[i+1])
            # First Test:
            i2 = thalist.extend(0, total)
            self.assertAlmostEqual(i2, len(thalist)-1)

            # Second Test:
            self.assertAlmostEqual(total, thalist.get_length(0,len(thalist)-1))

    def test_extend_case1(self):
        """First point within the list"""
        for thalist in self.vectors:
            start = random.random()*self.numpoints
            leng = random.random()*100-50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start="+str(start)+" and leng="+str(leng) +
                                   "\nresult: i2="+str(new)+" leng2="+str(leng2) +
                                   " dist="+str(Vector.norm(thalist[start] - thalist[new])))

    def test_extend_case2(self):
        """First Point before Start"""
        for thalist in self.vectors:
            start = -random.random()*30
            leng = leng = random.random()*100-50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start="+str(start)+" and leng="+str(leng) +
                                   "\nresult: i2="+str(new)+" leng2="+str(leng2) +
                                   " dist="+str(Vector.norm(thalist[start] - thalist[new])))

    def test_extend_case3(self):
        """First Point further than the end"""
        for thalist in self.vectors:
            start = self.numpoints + random.random()*50
            leng = random.random()*100-50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start="+str(start)+" and leng="+str(leng) +
                                   "\nresult: i2="+str(new)+" leng2="+str(leng2) +
                                   " dist="+str(Vector.norm(thalist[start] - thalist[new])))


class TestVector2D(TestVector3D):
    def setUp(self, dim=2):
        TestVector3D.setUp(self, dim)
        self.vectors = [Vector.Vectorlist2D(i.data) for i in self.vectors]

    def test_Cut(self):
        for thalist in self.vectors:
            i = random.random()*200-50
            dirr = [random.randint(0, 40), random.randint(-20, 20)]

            p1 = thalist[i]+dirr
            p2 = thalist[i]-dirr
            neu = thalist.cut(p1, p2, i)
            self.assertAlmostEqual(i, neu[1][0]+neu[1][1])



if __name__ == '__main__':
        unittest.main(verbosity=2)