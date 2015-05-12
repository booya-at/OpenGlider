from __future__ import division

from openglider.vector.spline.bezier import (
    Bezier, SymmetricBezier, BernsteinBase)
from openglider.vector.spline.bspline import (
    BSpline, SymmetricBSpline, BSplineBase)



# if __name__ == "__main__":
#     t = numpy.linspace(0, 1, 30)
#     curve = numpy.array(list(zip(t, numpy.sin(t))))
#     constraints = [[None] * 2 for i in range(5)]
#     constraints[0] = [1,0]
#     print(constraints[0])
#     a = Bezier()
#     print(a.constraint_fit(curve, constraints))