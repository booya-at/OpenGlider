from Profile import Profile2D
from Utils.Bezier import BezierCurve
from Vector import cut
import numpy
from Graphics import Line, Point, Graphics
import numpy as np
import scipy.interpolate as int
"""
a=Profile2D()
a.Import('freecad/glider/profiles/nase1.dat')
a.Normalize()
a.Numpoints=40

inter=int.splprep(a.Profile.transpose(),ub=100.,ue=100.,k=3)
bpoints=np.array(inter[0][1:2][0]).transpose()
print(bpoints)

bsp=np.array(int.splev(np.linspace(0,1,100),inter[0]))

Graphics([Line(a.Profile),Line(bsp.transpose()),Line(bpoints)])

print(inter[0])
"""



a=Profile2D()

a.Import('freecad/glider/profiles/nase1.dat')


a.Numpoints=15
b=BezierCurve()
b._numofbezierpoints=6
b.NumPoints=30
c=BezierCurve()
c._numofbezierpoints=5
c.NumPoints=30

#Graphics([Line(unten),Line(b.Points),Line(b.BezierPoints)])



####simon-test
p1=numpy.array([1.,0.])
p2=numpy.array([1.,1.])
p3=numpy.array([0.,0.])
p4=numpy.array([0.,3.])

print(cut((p1,p2),(p3,p4)))