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

    def _setBezierPoints(self,points):
        if len(points)==0:
            print('no points!')
            return
        elif Depth(points) != 3:
            print('depth of points is '+ str(Depth(points))+', but should be 3')
        else:
            self._BezierPoints = np.array(points)
            self._BezierFunction = BezierFunction(self.BezierPoints)

    def _getBezierPoints(self):
        return(self._BezierPoints)

    def _setNumpoints(self,num):
        self._numpoints=num

    def _getNumPoints(self):
        return self._numpoints

    def _getPoints(self):
        lin=np.linspace(0,1,self._numpoints)
        return np.array(map(self._BezierFunction,lin))

    def _setPoints(self,points,numofbezierpoints=7):
        fits = FitBezier(points,numofbezierpoints)
        print(fits)
        self._setBezierPoints(fits)

    def _setNumBezierPoints(self,num):
        print('sollte anzahl der bezierpunkte setzen')

    BezierPoints=property(_getBezierPoints,_setBezierPoints)
    Points=property(_getPoints,_setPoints)
    Numpoints=property(_getNumPoints,_setNumpoints)


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


def FitBezier(points,splines=3):
    """Fit to a given set of points with a certain number of spline-points (default=3)"""
    base=BernsteinBase(splines)
    matrix=np.matrix([[base[spalte](zeile*1./len(points)) for spalte in range(splines)] for zeile in range(len(points))])
    matrix=np.linalg.pinv(matrix)
    return np.array(matrix*points)
