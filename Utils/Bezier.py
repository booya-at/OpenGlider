import numpy as np
from scipy.misc import comb
import Graphics as G

def BernsteinBase(d):
    def BSF(m):
        return lambda x: comb(d, m)*(x**m)*((1-x)**(d-1-m))
    return [BSF(n)  for n in range(d)]

def BezierFunction(points):
    """"""
    base=BernsteinBase(len(points))
    def func(x):
        val=np.array([0, 0])
        for i in range(len(points)):
            fakt = base[i](x)
            v = np.array(points[i])*fakt
            val = val+v
        return val
    return func



def FitBezier(points,splines=3):
    """Fit to a given set of points with a certain number of spline-points (default=3)"""
    base=BernsteinBase(splines)
    matrix=np.matrix([[base[spalte](zeile*1./len(points)) for spalte in range(splines)] for zeile in range(len(points))])
    matrix=np.linalg.pinv(matrix)
    return matrix*points

if __name__ == "__main__":
#    import Graphics as G
    inp1=[[1.,0.],[0.2,0.08],[0.,0.03],[0.,0.]]
    inp2=[[1.,0.],[0.2,-0.05],[0.,-0.03],[0.,0.]]
    a=BernsteinBase(3)
    
    ab=(BezierFunction(inp1))
    pp=[ab(i*0.1) for i in range(11)]
    fitp=FitBezier(pp,4)
    fitp=np.round(np.array(fitp),3)
    print(fitp)
    G.Graphics([G.Line(pp),G.Line([])])
    G.Graphics([G.Line(np.array([[ 1. ,   -0.   ],
 [ 0.145,  0.088],
 [-0.024,  0.025],
 [ 0.002, -0.005]]))])
    
    
    xneu=np.linspace(0,1,100)
    a2=np.array(inp2)
    
    #a=G.Graphics([G.Point(tolist(np.transpose(b2))),G.Line(tolist(np.transpose(b1))),G.Line(inp1),G.Line(inp2)])