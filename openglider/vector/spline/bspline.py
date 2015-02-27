from openglider.vector.spline import BezierCurve


class BSplineBasis():
    def __init__(self, degree):
        self.degree = degree
        self.bases = {}

    def __call__(self, numpoints):
        if numpoints not in self.bases and True:
            knots = self.make_knot_vector(self.degree, numpoints)
            basis = [self.get_basis(self.degree, i, knots) for i in range(numpoints)]
            self.bases[numpoints] = basis

        return self.bases[numpoints]

    def get_basis(self, degree, i, knots):
        """ Returns a basis_function for the given degree """
        if degree == 0:

            def basis_function(t):
                """The basis function for degree = 0 as per eq. 7"""
                t_this = knots[i]
                t_next = knots[i+1]
                out = 1. if (t>=t_this and t< t_next) else 0.
                return out
        else:

            def basis_function(t):
                """The basis function for degree > 0 as per eq. 8"""
                out = 0.
                t_this = knots[i]
                t_next = knots[i+1]
                t_precog  = knots[i+degree]
                t_horizon = knots[i+degree+1]

                top = (t-t_this)
                bottom = (t_precog-t_this)

                if bottom != 0:
                    out = top/bottom * self.get_basis(degree-1, i, knots)(t)

                top = (t_horizon-t)
                bottom = (t_horizon-t_next)
                if bottom != 0:
                    out += top/bottom * self.get_basis(degree-1, i+1, knots)(t)

                return out

        return basis_function



    def make_knot_vector(self, degree, num_points):
        """
        Create knot vectors
        """

        total_knots = num_points+degree+1
        outer_knots = degree
        inner_knots = total_knots - 2*outer_knots

        knots = [0.]*outer_knots
        knots += [i/(inner_knots-1) for i in range(inner_knots)]
        knots += [1.]*outer_knots
        return knots


class BSplineCurve(BezierCurve):
    basefactory = BSplineBasis(2)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import numpy

    data = [(3, -1), (2.5, 3), (0, 1), (-2.5, 3), (-3, -1)]
    curve = BSplineCurve(data)

    values = [t for t in numpy.linspace(0, 1, 1000)]#, endpoint=C.endpoint)]

    fig = plt.figure()
    interpolation_curve = [curve(s) for s in values]
    ax = fig.add_subplot(111)

    ax.plot(*zip(*interpolation_curve), alpha=0.5)
    ax.plot(*zip(*data), alpha=0.3)

    plt.show()




