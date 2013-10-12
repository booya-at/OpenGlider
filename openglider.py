from Profile import Profile2D
#from Utils.Bezier import BezierCurve
from Vector import cut
import numpy
#from Graphics import Line, Point, Graphics
import numpy as np
import scipy.interpolate as int



####simon-test
p1=numpy.array([1.,0.])
p2=numpy.array([1.,1.])
p3=numpy.array([0.,0.])
p4=numpy.array([0.,3.1])



try:
    ab=cut(p1,p2,p3,p4)
except numpy.linalg.linalg.LinAlgError:
    print("jojo")


def testfunktion(*args):
    if not args:
        print("nixda")
    else:
        print(len(args))
        print(args.__class__)

testfunktion()
testfunktion("ab",[1,2,3])
testfunktion([1,2,3])

prof=Profile2D()
prof.Import("/home/simon/test.dat")