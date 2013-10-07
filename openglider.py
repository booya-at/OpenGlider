from Profile import Profile2D
from Utils.Bezier import BezierCurve
from Graphics import Line, Point, Graphics
import numpy as np

a=Profile2D()
a.Import('freecad/glider/profiles/nase1.dat')
c=np.array([[1.,0.],[2.,1.],[5,1],[1,-1]])
b=BezierCurve()
b.Points=a.Profile[0:a.Numpoints/2]
print(b.Points)

Graphics([Line(b.Points),Line(b.BezierPoints),Line(a.Profile)])
