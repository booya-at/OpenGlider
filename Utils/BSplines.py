import numpy as np
import scipy
from Vector import Depth

def choose(n, k):
    if 0 <= k <= n:
        p = 1.
        for t in xrange(min(k, n - k)):
            p = (p * (n - t)) // (t + 1)
        return p
    else:
        return 0

class bernsteinbasis():
    def __init__(self,d):
        self.d=d

    def _setn(self,n):
        self.n=n
        self.binom=choose(self.d,self.n)
        self.dmn=self.d-self.n

    def calc(self,x):
        return(self.binom*x**self.n*(1-x)**self.dmn)

class bspline(bernsteinbasis):
    def __init__(self,points,df=3):
        self.points=np.array(points)
        self.length=len(points)
        bernsteinbasis.__init__(self,df)

    def getpoint(self,x):
        if isinstance(x,np.ndarray):
            self.x=x
        elif isinstance(x,list):
            self.x=np.array(x)
        else:
            self.x=np.array([x])
        self.temp=[]
        for j in range(self.length):
            self._setn(j)
            self.temp.append(map(self.calc,self.x))
        self.out=np.dot(np.array(self.temp).transpose(),np.array(self.points))
        self.out.transpose()
        return([i.flatten() for i in self.out.transpose()])

def tolist(nparray):
    return([test(i) for i in nparray])

def test(ding):
    if Depth(ding) > 1:
        return(tolist(ding))
    else:
        return(ding)

def getBSplinePoint(points,df=3):
    b


if __name__ == "__main__":
    import Graphics as G
    inp1=[[1.,0.],[0.2,0.08],[0.,0.03],[0.,0.]]
    inp2=[[1.,0.],[0.2,-0.05],[0.,-0.03],[0.,0.]]
    a1=bspline(inp1,df=3)
    a2=bspline(inp2)
    xneu=np.linspace(0,1,100)
    b1=a1.getpoint(xneu)
    a1=np.array(inp1)
    b2=a2.getpoint(xneu)
    a2=np.array(inp2)
    
    a=G.Graphics([G.Point(np.transpose(b2)),G.Line(np.transpose(b1)),G.Line(inp1),G.Line(inp2)])