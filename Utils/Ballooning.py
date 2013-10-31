__author__ = 'simon'

import numpy
from scipy.interpolate import interp1d
from openglider.Utils.Bezier import BezierCurve
#TODO ballooning -> amount (total(integral),maximal)


class Ballooning(object):
    def __init__(self, points=[[[0, 0], [0.2, 0.14], [0.8, 0.14], [1, 0]],
                               [[0, 0], [0.2, -0.14], [0.8, -0.14], [1, 0]]]):
        self.upper = BezierCurve(points[0])
        self.lower = BezierCurve(points[1])
        self.upfit = self.upper.interpolation()
        self.lowfit = self.lower.interpolation()
        print(self.upfit.x[0], self.upfit.x[-1])

    def __getitem__(self, xval):
        if -1 <= xval < 0:
            #return self.upper.xpoint(-xval)[1]
            return self.upfit(-xval)
        elif 0 <= xval <= 1:
            #return -self.lower.xpoint(xval)[1]
            return -self.lowfit(xval)
        else:
            ValueError("Ballooning only between -1 and 1")

    def get(self, xval):
        return self.phi(1./(self.__getitem__(xval)+1.))

    @staticmethod
    def phi(*baloon):
        """Return the angle of the piece of cake.
        b/l=R*phi/(R*Sin(phi)) -> Phi=arsinc(l/b)"""
        global phiinterpolation
        if not phiinterpolation:
            interpolate()
        return phiinterpolation(baloon)




    def mapx(self, xvals):
        return [self[i] for i in xvals]

    def amount_maximal(self):
        pass

    def amount_integral(self):
        pass

    def amount_set(self,amount):
        factor = float(amount)/self.Amount
        self.upper.ControlPoints = [i*[1, factor] for i in self.upper.ControlPoints]
        self.lower.ControlPoints = [i*[1, factor] for i in self.lower.ControlPoints]

    Amount = property(amount_integral, amount_set)


phiinterpolation = None


def interpolate(numpoints=1000, phi0=0, phi1=numpy.pi/2):
    global phiinterpolation
    (x, y) = ([], [])
    for i in range(numpoints+1):
        phi = phi0+(1-i*1./numpoints)*(phi1-phi0)  # reverse for interpolation (increasing x_values)
        x.append(numpy.sinc(phi))
        y.append(phi)
    phiinterpolation = interp1d(x, y)

interpolate()
phiinterpolation