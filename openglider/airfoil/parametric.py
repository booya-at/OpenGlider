import numpy
import scipy.interpolate
from openglider.airfoil import Profile2D
from openglider.utils.bezier import BezierCurve
from openglider.vector import norm


class BezierProfile2D(Profile2D):
    # TODO make new fit bezier method to set the second x value of the
    # controllpoints to zero.
    def __init__(self, data=None, name=None, normalize_root=True,
                 upper_spline=None, lower_spline=None):
        super(BezierProfile2D, self).__init__(data=data, name=name,
                                       normalize_root=normalize_root)
        self.close()
        self.normalize()
        self.upper_spline = upper_spline or self.fit_upper()
        self.lower_spline = lower_spline or self.fit_lower()

    def __json__(self):
        dct = super(BezierProfile2D, self).__json__()
        dct.update({'upper_spline': self.upper_spline,
                    'lower_spline': self.lower_spline})
        return dct

    @classmethod
    def __from_json__(cls, rootprof, data, name, upper_spline, lower_spline):
        profile = super(BezierProfile2D, cls).__from_json__(
            rootprof, data, name)
        profile.upper_spline = upper_spline
        profile.lower_spline = lower_spline
        return profile

    def fit_upper(self, num=100, dist=None, control_num=6):
        upper = self.data[:self.noseindex + 1]
        upper_smooth = self.make_smooth_dist(upper, num, dist)
        #upper_smooth = [self[self(x)] for x in numpy.linspace(-1., 0., num=num)]
        return BezierCurve.fit(upper_smooth, numpoints=control_num)

    def fit_lower(self, num=100, dist=None, control_num=6):
        lower = self.data[self.noseindex:]
        lower_smooth = self.make_smooth_dist(lower, num, dist, upper=False)
        #lower_smooth = [self[self(x)] for x in numpy.linspace(0., 1., num=num)]
        return BezierCurve.fit(lower_smooth, numpoints=control_num)

    def fit_region(self, start, stop, num_points, control_points):
        smoothened = [self[self(x)] for x in numpy.linspace(start, stop, num=num_points)]
        return BezierCurve.fit(smoothened, numpoints=num_points)

    def fit_profile(self, num_points, control_points):
        self.upper_spline = self.fit_region(-1., 0., num_points, control_points)
        self.lower_spline = self.fit_region(0., 1., num_points, control_points)

    def apply_splines(self, num=70):
        upper = self.upper_spline.get_sequence(num)
        lower = self.lower_spline.get_sequence(num)
        self.data = numpy.array(upper.tolist() + lower[1:].tolist())

    def make_smooth_dist(self, points, num=70, dist=None, upper=True):
        # make array [[lenght, x, y], ...]
        length = [0]
        for i, point in enumerate(points[1:]):
            length.append(length[-1] + norm(point - points[i]))
        interpolation = scipy.interpolate.interp1d(length, numpy.array(points).T)
        if dist == "const":
            dist = numpy.linspace(0, length[-1], num)
        elif dist == "sin":
            if upper:
                dist = [numpy.sin(i) * length[-1] for i in numpy.linspace(0, numpy.pi / 2, num)]
            else:
                dist = [abs(1 - numpy.sin(i)) * length[-1] for i in numpy.linspace(0, numpy.pi / 2, num)]
        elif dist == "hardcore":
            # berechne kruemmung in den punkten
            pass
        else:
            return points
        return [interpolation(i) for i in dist]


