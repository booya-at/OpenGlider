import numpy as np
from scipy.misc import comb
from Vector import Depth
import Graphics as G




class BezierCurve(object):
    def __init__(self,points=[]):
        self._setBezierPoints(points)
        self._numpoints=20
        self._BezierPoints=None
        self._BezierFunction=None
        self._numofbezierpoints=4

    def _setBezierPoints(self,points):
        if len(points)==0:
            print('no points!')
            return
        elif Depth(points) != 3:
            print('depth of points is '+ str(Depth(points))+', but should be 3')
        else:
            self._BezierPoints = np.array(points)
            self._BezierFunction = BezierFunction(self.BezierPoints)
            self._numofbezierpoints=len(points)

    def _getBezierPoints(self):
        return(self._BezierPoints)

    def _setNumpoints(self,num):
        self._numpoints=num

    def _getNumPoints(self):
        return self._numpoints

    def _getPoints(self):
        lin=np.linspace(0,1,self._numpoints)
        return np.array(map(self._BezierFunction,lin))

    def _setPoints(self,points):
        fits = FitBezier(points,self._numofbezierpoints)
        self._setBezierPoints(fits)


    def _getNumBezierPoints(self):
        return self._numofbezierpoints

    BezierPoints=property(_getBezierPoints,_setBezierPoints)
    Points=property(_getPoints,_setPoints)
    NumPoints=property(_getNumPoints,_setNumpoints)


def BernsteinBase(d):
    def BSF(n):
        return lambda x: comb(d-1,n)*(x**n)*((1-x)**(d-1-n))
    return [BSF(n)  for n in range(d)]

def BezierFunction(points):
    """"""
    base=BernsteinBase(len(points))
    def func(x):
        val=np.zeros(len(points[0]))
        for i in range(len(points)):
            fakt=base[i](x)
            v=np.array(points[i])*fakt
            val=val+v
        return val
    return func


def FitBezier(points,splines=3, start=True, end=True):
    """Fit to a given set of points with a certain number of spline-points (default=3)
    if start (/ end) is True, the first (/ last) point of the Curve is included"""
    base=BernsteinBase(splines)
    matrix=np.matrix([[base[spalte](zeile*1./(len(points)-1)) for spalte in range(splines)] for zeile in range(len(points))])
    matrix=np.linalg.pinv(matrix)
    out = np.array(matrix*points)
    if start:
        out[0]=points[0]
    if end:
        out[-1]=points[-1]
    return(out)
