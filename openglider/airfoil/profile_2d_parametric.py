import numpy as np

import euklid

from openglider.airfoil import Profile2D

# TODO: FIX!

class BezierProfile2D(Profile2D):
    # TODO make new fit bezier method to set the second x value of the
    # controllpoints to zero.
    def __init__(self, data=None, name=None,
                 upper_spline=None, lower_spline=None,
                 control_num_lower=8, control_num_upper=8):
        super(BezierProfile2D, self).__init__(data=data, name=name)
        self.curve = self.normalized().curve
        self.upper_spline = upper_spline
        self.lower_spline = lower_spline

        self.apply_splines()

    def __json__(self):
        dct = super(BezierProfile2D, self).__json__()
        dct.update({'upper_spline': self.upper_spline,
                    'lower_spline': self.lower_spline})
        return dct

    def fit_upper(self, num=100, dist=None, control_num=8):
        upper = self.curve.nodes[:self.noseindex + 1]
        upper_smooth = self.make_smooth_dist(upper, num, dist)
        constraints = [[None] * 2 for i in range(control_num)]
        constraints[0] = [1., 0.]
        constraints[-2][0] = 0.
        constraints[-1] = [0., 0.]
        if self.upper_spline:
            return self.upper_spline.__class__.constraint_fit(upper_smooth, constraints)
        else:
            return euklid.spline.BSplineCurve.constraint_fit(upper_smooth, constraints)

    def fit_lower(self, num=100, dist=None, control_num=8):
        lower = self.curve.nodes[self.noseindex:]
        lower_smooth = self.make_smooth_dist(lower, num, dist, upper=False)
        constraints = [[None] * 2 for i in range(control_num)]
        constraints[-1] = [1, 0]
        constraints[1][0] = 0
        constraints[0] = [0, 0]
        if self.lower_spline:
            return self.lower_spline.__class__.constraint_fit(lower_smooth, constraints)
        else:
            return euklid.spline.BSplineCurve.constraint_fit(lower_smooth, constraints)

    def fit_region(self, start, stop, num_points, control_points):
        smoothened = [self[self(x)] for x in np.linspace(start, stop, num=num_points)]
        return euklid.spline.Bezier.fit(smoothened, numpoints=num_points)

    def fit_profile(self, num_points, control_points):
        # todo: classmethod
        self.upper_spline = self.fit_region(-1., 0., num_points, control_points)
        self.lower_spline = self.fit_region(0., 1., num_points, control_points)

    def apply_splines(self, num=70):
        upper = self.upper_spline.get_sequence(num)
        lower = self.lower_spline.get_sequence(num)
        self.data = np.array(upper.tolist() + lower.tolist()[1:])

    def make_smooth_dist(self, points, num=70, dist=None, upper=True):
        # make array [[length, x, y], ...]
        if not dist:
            return points
        length = [0]
        for i, point in enumerate(points[1:]):
            length.append(length[-1] + (point - points[i]).length())
        interpolation_x = euklid.vector.Interpolation(list(zip(length, [p[0] for p in points])))
        interpolation_y = euklid.vector.Interpolation(points)

        def get_point(dist):
            x = interpolation_x.get_value(dist)
            return [x, interpolation_y.get_value(x)]

        if dist == "const":
            dist = np.linspace(0, length[-1], num)
        elif dist == "sin":
            if upper:
                dist = [np.sin(i) * length[-1] for i in np.linspace(0, np.pi / 2, num)]
            else:
                dist = [abs(1 - np.sin(i)) * length[-1] for i in np.linspace(0, np.pi / 2, num)]
        else:
            return points
        return [get_point(d) for d in dist]

    @classmethod
    def from_profile_2d(cls, profile_2d):
        return cls(profile_2d.data, profile_2d.name)
