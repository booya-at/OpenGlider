import numpy as np
from scipy.misc import comb
import Graphics as G

def BernsteinBase(d):
    def BSF(n):
        return lambda x: comb(d,n)*(x**n)*((1-x)**(d-1-n))
    return [BSF(n)  for n in range(d)]

def BezierFunction(points):
    """"""
    base=BernsteinBase(len(points))
    def func(x):
        val=np.array([0,0])
        for i in range(len(points)):
            fakt=base[i](x)
            v=np.array(points[i])*fakt
            val=val+v
        return val
    return func



def FitBezier(points,splines=3):
    """Fit to a given set of points with a certain number of spline-points (default=3)"""
    base=BernsteinBase(splines)
    matrix=np.matrix([[base[spalte](zeile*1./len(points)) for spalte in range(splines)] for zeile in range(len(points))])
    matrix=np.linalg.pinv(matrix)
    return matrix*points
