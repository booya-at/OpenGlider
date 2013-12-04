__author__ = 'simon'
import unittest
import random

from openglider import Vector

class TestVector(unittest.TestCase):

    def setUp(self):
        self.vectors = []
        self.sums = []
        numlists = 100
        self.numpoints = numpoints = 100
        for i in range(numlists):
            #make the points
            pointlist = []
            for u in range(numpoints):
                pointlist.append([random.random()*100, random.random()*100])
            self.vectors.append(Vector.Vectorlist(pointlist))
        # Cases

    def test_total(self):
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

    def test_case1(self):
        """First point within the list"""
        for thalist in self.vectors:
            start = random.random()*self.numpoints
            leng = random.random()*100-50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start="+str(start)+" and leng="+str(leng) +
                                   "\nresult: i2="+str(new)+" leng2="+str(leng2))

    def test_case2(self):
        """First Point before Start"""
        for thalist in self.vectors:
            start = -random.random()*30
            leng = leng = random.random()*100-50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start="+str(start)+" and leng="+str(leng) +
                                   "\nresult: i2="+str(new)+" leng2="+str(leng2))

    def test_case3(self):
        """First Point further than the end"""
        for thalist in self.vectors:
            start = self.numpoints + random.random()*50
            leng = random.random()*100-50
            new = thalist.extend(start, leng)
            leng2 = thalist.get_length(start, new)
            self.assertAlmostEqual(abs(leng), leng2, 7,
                                   "Failed for start="+str(start)+" and leng="+str(leng) +
                                   "\nresult: i2="+str(new)+" leng2="+str(leng2))




if __name__ == '__main__':
        unittest.main(verbosity=2)