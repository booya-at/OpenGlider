__author__ = 'simon'

import numpy
from scipy.interpolate import interp1d
from openglider.Utils.Bezier import BezierCurve
#TODO ballooning -> amount (total(integral),maximal)


class Ballooning(object):
    def __init__(self, f_upper, f_lower):
        self.upper = f_upper
        self.lower = f_lower

    def __getitem__(self, xval):
        """Get Ballooning Value (%) for a certain XValue"""
        if -1 <= xval < 0:
            #return self.upper.xpoint(-xval)[1]
            return self.upper(-xval)
        elif 0 <= xval <= 1:
            #return -self.lower.xpoint(xval)[1]
            return self.lower(xval)
        else:
            ValueError("Ballooning only between -1 and 1")

    def __call__(self, arg):
        """Get Ballooning Arc (phi) for a certain XValue"""
        return self.phi(1./(self[arg]+1))

    def __add__(self, other):
        """Add another Ballooning to this one, needed for merging purposes"""
        xup = self.upper.x  # This is valid for scipy interpolations, no clue how to do different, if so...
        xlow = self.lower.x
        yup = [self.upper(i)+other.upper(i) for i in xup]
        ylow = [self.lower(i)+other.lower(i) for i in xlow]

        return Ballooning(interp1d(xup, yup), interp1d(xlow, ylow))

    def __mul__(self, other):
        """Multiply Ballooning With a Value"""
        up = self.upper.copy
        low = self.lower.copy
        up.y = [i*other for i in up.y]
        low.y = [i*other for i in low.y]
        return Ballooning(up, low)

    def copy(self):
        return Ballooning(self.upper, self.lower)

    @staticmethod
    def phi(*baloon):
        """Return the angle of the piece of cake.
        b/l=R*phi/(R*Sin(phi)) -> Phi=arsinc(l/b)"""
        global arsinc
        if not arsinc:
            interpolate_asinc()
        return arsinc(baloon)

    def mapx(self, xvals):
        return [self[i] for i in xvals]

    def amount_maximal(self):
        return max(max(self.upper.y), max(self.lower.y))

    def amount_integral(self):
        # Integration of 2-points allways:
        amount = 0
        for curve in [self.upper, self.lower]:
            for i in range(len(curve.x)-2):
                # points: (x1,y1), (x2,y2)
                #     _ p2
                # p1_/ |
                #  |   |
                #  |___|
                amount += (curve.y[i]+(curve.y[i+1]-curve.y[i])/2)*(curve.x[i+1]-curve.x[i])
        return amount/2

    def amount_set(self, amount):
        factor = float(amount)/self.Amount
        self.upper.y = [i*factor for i in self.upper.y]
        self.lower.y = [i*factor for i in self.lower.y]

    Amount = property(amount_maximal, amount_set)


class BallooningBezier(Ballooning):
    def __init__(self, points=[[[0, 0], [0.1,0], [0.2, 0.14], [0.8, 0.14], [0.9,0], [1, 0]],
                               [[0, 0], [0.1,0], [0.2, 0.14], [0.8, 0.14], [0.9,0], [1, 0]]]):
        self.upbez = BezierCurve(points[0])
        self.lowbez = BezierCurve(points[1])
        Ballooning.__init__(self, self.upbez.interpolation(), self.lowbez.interpolation())

    def __mul__(self, other):  # TODO: Check consistency
        """Multiplication of BezierBallooning"""
        # Multiplicate as normal interpolated ballooning, then refit
        Ballooning.__mul__(self, other)
        self.upbez.fit(numpy.transpose([self.upper.x, self.upper.y]))
        self.lowbez.fit(numpy.transpose([self.lower.x, self.lower.y]))

    def _setnumpoints(self, numpoints):
        Ballooning.__init__(self, self.upbez.interpolation(numpoints), self.lowbez.interpolation(numpoints))

    def _getnumpoints(self):
        return len(self.upper)

    Numpoints = property(_getnumpoints, _setnumpoints)


global arsinc
arsinc = None


def interpolate_asinc(numpoints=1000, phi0=0, phi1=numpy.pi):
    """Set Global Interpolation Function arsinc"""
    global arsinc
    (x, y) = ([], [])
    for i in range(numpoints+1):
        phi = phi1+(i*1./numpoints)*(phi0-phi1)  # reverse for interpolation (increasing x_values)
        x.append(numpy.sinc(phi/numpy.pi))
        y.append(phi)
    arsinc = interp1d(x, y)

# TODO: Do only when needed!
interpolate_asinc()