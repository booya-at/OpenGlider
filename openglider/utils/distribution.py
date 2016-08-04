from __future__ import division

import numpy

from openglider.utils.cache import HashedList


class Distribution(HashedList):
    @classmethod
    def new(cls, numpoints=20, dist_type=None, fixed_nodes=None, **kwargs):
        """
        create a new distribution
        Distribution.new(num_points=20, dist_type="cos", fixed_nodes=[-0.2, 0.2])
            -> list of 20 cos-distributed values, with shifted values so the given fixed_nodes are included in the set
        dist_type:
            * linear (default)
            * cos
            * cos_2
            * nose_cos
        """

        _types = {
            "cos": cls.from_cos_distribution,
            "cos_2": cls.from_cos_2_distribution,
            "nose_cos": cls.from_nose_cos_distribution
        }
        dist_func = _types.get(dist_type, cls.from_linear)
        dist = dist_func(numpoints, **kwargs)
        if fixed_nodes:
            dist.insert_values(fixed_nodes)

        return dist

    def get_index(self, x):
        i = x_last = x_this = -1
        for i, x_this in enumerate(self.data):
            if x_this >= x:
                break
            x_last = x_this

        dist = (x - x_last) / (x_this - x_last)

        return i + dist

    def find_nearest(self, x, start_ind=0):
        index = self.get_index(x)
        nearest = round(index)
        while nearest <= start_ind:
            nearest += 1

    def insert_value(self, value, start_ind=0, to_nose=True):

        if start_ind  >= len(self.data):
            self.data = list(self.data[:-1]) + [value] + [self.data[-1]]
            return start_ind + 1

        nearest_ind = numpy.abs(self.data[start_ind:] - value).argmin() + 1 + start_ind
        nose_ind = numpy.abs(self.data[start_ind:]).argmin() + start_ind

        if nearest_ind == len(self.data):
            self.data = list(self.data[:-1]) + [value] + [self.data[-1]]
            return nearest_ind

        # addition: tranform only from or to nose
        if value < 0 and to_nose is True:
            end_index = nose_ind
        else:
            end_index = None

        if value > 0 and self.data[start_ind] < 0 and to_nose is True:
            start_ind = nose_ind


        l1 = self.data[:start_ind]
        l2 = self.data[start_ind:nearest_ind]
        l3 = self.data[nearest_ind:end_index]
        if end_index:
            l4 = self.data[end_index:]
        else:
            l4 = []

        # shift all values after the insert value
        if len(l3) > 0:
            l3 = (l3 - l3[-1]) * (l3[-1] - value) / (l3[-1] - l2[-1]) + l3[-1]

        # shift all values left to the insert value to match: l2[-1] == value
        if len(l2) < 2:
            l2 = [value]
        else:
            l2 = (l2 - l2[0]) * (value - l2[0]) / (l2[-1] - l2[0]) + l2[0]
        self.data = list(l1) + list(l2) + list(l3) + list(l4)
        return nearest_ind

    def insert_values(self, values):
        """
        values: list of values to insert
        shift the data to match values
        """
        start_ind = 0
        values = [i for i in values if (i != 1 and i != -1)]
        values = list(set(values))       # delete duplicate and sort -1...1
        values.sort()
        for value in values:
            start_ind = self.insert_value(value, start_ind)

    @classmethod
    def from_linear(cls, numpoints, start = -1, stop = 1):
        """
        Get a linear distribution
        """
        return cls(numpy.linspace(start, stop, numpoints))

    @classmethod
    def from_polynom_distribution(cls, numpoints, order=2):
        """
        return a polynom distribution
        f(x) = +- x^p, 0 < x < 1
        """
        half_numpoints = int(numpoints/2) + 1
        second_half = [i/half_numpoints ** order for i in range(half_numpoints)]
        first_half = [-x for x in second_half[::-1]][:-1]

        return cls(first_half + second_half)

    @classmethod
    def from_cos_distribution(cls, numpoints):
        """
        return cosinus distributed x-values
        low density at (-1) and (+1) but neat around 0
        """
        numpoints -= numpoints % 2  # brauchts?
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 - numpy.sin(numpy.pi * x))
        return cls([xtemp(i/numpoints) for i in range(numpoints+1)])

    @classmethod
    def from_cos_2_distribution(cls, numpoints, arg=None):
        """
        return cosinus distributed x-values
        double-cosinus -> neat distribution at nose and trailing edge
        """
        numpoints -= numpoints % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 + numpy.cos(2 * numpy.pi * x)) / 2
        return cls([xtemp(i/numpoints) for i in range(numpoints+1)])

    @classmethod
    def from_nose_cos_distribution(cls, numpoints, border=0.5):
        """
        from cos distribution at leading edge, to a const distribution at +- 1
        """

        def f(x):
            return x ** 2 / ((-2 + border) * border) if x < border else (2 * x - border)/(-2 + border)

        dist_values = numpy.linspace(0, 1, int(numpoints / 2) + 1)
        first_half = [f(val) for val in dist_values[::-1][:-1]]
        second_half = [-f(val) for val in dist_values]

        return cls(first_half + second_half)

    def add_glider_fixed_nodes(self, glider):
        insert_pts = [-abs(point.rib_pos) for point in glider.attachment_points] + [0]
        self.insert_values(insert_pts)
        self.data = self.upper + [-i for i in reversed(self.upper[:-1])]

    @property
    def upper(self):
        out = []
        i = 0
        while True:
            out.append(self.data[i])
            i += 1
            if self.data[i] > 0:
                break
        return out


if __name__ == "__main__":
    a = Distribution.new(30, "cos", fixed_nodes=[-0.99, -0.98, -0.97, -0.9, -0.1, 0.333, 0.9, 0.95, 0.96, 0.97])
    print(a.data)
