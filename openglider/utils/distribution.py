from __future__ import division

import numpy

from openglider.utils.cache import HashedList


class distribution(HashedList):
    def __init__(self, numpoints=20, dist_type=None, fix_points=[], type_arg=None):
        """
        distribution(num_points=20, type="cos", fix_points=[], dist_arg=None)
            return a list of ordered values between -1, 1 with the given fix_points
        type: (None -> constant difference, cos", "cos_2", "nose_cos")
        dist_arg: pass an additional argument"""

        self.data = self._values(dist_type, numpoints, type_arg)
        if fix_points:
            self._insert_values(fix_points)

    def _values(self, dist_type, numpoints, type_arg):
        types = {
            "cos": self.cos_distribution,
            "cos_2": self.cos_2_distribution,
            "nose_cos": self.nose_cos_distribution
        }
        return types.get(dist_type, self.std_distribution)(numpoints, type_arg)

    def _insert_values(self, values):

        def _insert_value(value, start_ind=0):
            # find the nearest value:
            nearest_ind = numpy.abs(self.data[start_ind:] - value).argmin() + 1 + start_ind
            l1 = self.data[:start_ind]
            l2 = self.data[start_ind:nearest_ind]
            l3 = self.data[nearest_ind:]
            l3 = (l3 - l3[-1]) * (l3[-1] - value) / (l3[-1] - l2[-1]) + l3[-1]
            if len(l2) < 2:
                l2 = [value]
            else:
                l2 = (l2 - l2[0]) * (value - l2[0]) / (l2[-1] - l2[0]) + l2[0]
            self.data = list(l1) + list(l2) + list(l3)
            return nearest_ind

        start_ind = 0
        for value in values:
            start_ind = _insert_value(value, start_ind)

    @staticmethod
    def cos_distribution(numpoints, arg=None):
        """
        return cosinus distributed x-values
        """
        numpoints -= numpoints % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 - numpy.sin(numpy.pi * x))
        return [xtemp(i/numpoints) for i in range(numpoints+1)]

    @staticmethod
    def cos_2_distribution(numpoints, arg=None):
        """
        return cosinus distributed x-values
        double-cosinus -> neat distribution at nose and trailing edge
        """
        numpoints -= numpoints % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 + numpy.cos(2 * numpy.pi * x)) / 2
        return [xtemp(i/numpoints) for i in range(numpoints+1)]

    @staticmethod
    def nose_cos_distribution(numpoints, arg=None):
        """from cos distribution at leading edge, to a const distribution ad trailing edge"""
        arg = arg or 0.5
        def distribution(numpoints):
            def f(x):
                return x ** 2 / ((-2 + arg) * arg) if x < arg else (2 * x - arg)/(-2 + arg)
            dist_values = numpy.linspace(0, 1, int(numpoints / 2) + 1)
            dist_values = [f(val) for val in dist_values]
            dist_values = dist_values[::-1][:-1] + list(-numpy.array(dist_values))
            return dist_values
        return distribution(numpoints)

    @staticmethod
    def std_distribution(numpoints, arg=None):
        return numpy.linspace(-1, 1, numpoints)
