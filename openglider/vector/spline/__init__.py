from __future__ import division

from openglider.vector.spline.bezier import (
    Bezier, SymmetricBezier, BernsteinBase)
from openglider.vector.spline.bspline import (
    BSpline, SymmetricBSpline, BSplineBase)


class GenericSpline(Bezier):
    def __json__(self):
        out = super(GenericSpline, self).__json__()
        if hasattr(self.basefactory, "degree"):
            out["degree"] = self.basefactory.degree
        else:
            out["degree"] = 0
        return out

    @classmethod

    def __from_json__(cls, controlpoints, degree=0):
        obj = super(GenericSpline, cls).__from_json__(controlpoints)
        if degree == 0:
            obj.basefactory = BernsteinBase
        else:
            obj.basefactory = BSplineBase(degree)
        return obj


class SymmetricGenericSpline(SymmetricBezier):
    def __json__(self):
        out = super(SymmetricGenericSpline, self).__json__()
        if hasattr(self.basefactory, "degree"):
            out["degree"] = self.basefactory.degree
        else:
            out["degree"] = 0
        return out

    @classmethod

    def __from_json__(cls, controlpoints, degree=0):
        obj = super(SymmetricGenericSpline, cls).__from_json__(controlpoints)
        if degree == 0:
            obj.basefactory = BernsteinBase
        else:
            obj.basefactory = BSplineBase(degree)
        return obj

# if __name__ == "__main__":
#     t = np.linspace(0, 1, 30)
#     curve = np.array(list(zip(t, np.sin(t))))
#     constraints = [[None] * 2 for i in range(5)]
#     constraints[0] = [1,0]
#     print(constraints[0])
#     a = Bezier()
#     print(a.constraint_fit(curve, constraints))