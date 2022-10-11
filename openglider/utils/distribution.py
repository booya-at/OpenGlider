from __future__ import annotations
from typing import Callable, List
import numpy as np

from openglider.utils.cache import HashedList


class Distribution(HashedList):
    data: List[float]
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
            self.data = np.array(list(self.data[:-1]) + [value] + [self.data[-1]])
            return start_ind + 1

        nearest_ind = np.abs(self.data[start_ind:] - value).argmin() + 1 + start_ind
        nose_ind = np.abs(self.data[start_ind:]).argmin() + start_ind

        if nearest_ind == len(self.data):
            self.data = list(self.data[:-1]) + [value] + [self.data[-1]]
            return nearest_ind

        # addition: transform only from or to nose
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
    def from_linear(cls, numpoints, start=-1, stop=1) -> Distribution:
        """
        Get a linear distribution
        """
        return cls([start + (stop - start)/(numpoints-1) * i for i in range(numpoints)])

    @classmethod
    def from_polynom_distribution(cls, numpoints, order=2) -> Distribution:
        """
        return a polynom distribution
        f(x) = +- x^p, 0 < x < 1
        """
        half_numpoints = int(numpoints/2) + 1
        second_half = [i/half_numpoints ** order for i in range(half_numpoints)]
        first_half = [-x for x in second_half[::-1]][:-1]

        return cls(first_half + second_half)

    @classmethod
    def from_cos_distribution(cls, numpoints) -> Distribution:
        """
        return cosinus distributed x-values
        low density at (-1) and (+1) but neat around 0
        """
        numpoints -= numpoints % 2  # brauchts?
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 - np.sin(np.pi * x))
        return cls([xtemp(i/numpoints) for i in range(numpoints+1)])

    @classmethod
    def from_cos_2_distribution(cls, numpoints, arg=None) -> Distribution:
        """
        return cosinus distributed x-values
        double-cosinus -> neat distribution at nose and trailing edge
        """
        numpoints -= numpoints % 2
        xtemp = lambda x: ((x > 0.5) - (x < 0.5)) * (1 + np.cos(2 * np.pi * x)) / 2
        return cls([xtemp(i/numpoints) for i in range(numpoints+1)])

    @classmethod
    def create_cos_distribution(cls, factor: float) -> Callable:
        def new_distribution(parent, numpoints, *arg, **kwarg):
            numpoints -= numpoints % 2
            
            xtemp = lambda x: ((x<=0)-(x>0))*(factor*np.cos(x*0.5*np.pi)+(1-factor)*(1-abs(x))-1)
            data = [xtemp(2*i/numpoints-1) for i in range(numpoints+1)]
            data[0] = -1
            data[-1] = 1
            return cls(data)
        
        return new_distribution

    @classmethod
    def create_cos_distribution_2(cls, factor_front: float, factor_back) -> Callable:
        def new_distribution(parent, numpoints, *arg, **kwarg):
            numpoints -= numpoints % 2
            
            factor_linear = 1-factor_back-factor_front

            x = lambda i: 2*i/numpoints - 1
            cos_front_def = lambda x:((x<=0)-(x>0)) * (np.cos(0.5 * np.pi * x)-1)

            #((x > 0.5) - (x < 0.5)) * (1 + np.cos(2 * np.pi * x)) / 2
            cos_back_def = lambda x: ((x>=0)-(x<0))*0.5*(np.cos(np.pi * (x+1))+1)
            
            data = [factor_front*cos_front_def(x(i)) + factor_back*cos_back_def(x(i)) + factor_linear*x(i) for i in range(numpoints+1)]

            return cls(data)
        
        return new_distribution

    @classmethod
    def from_nose_cos_distribution(cls, numpoints, border=0.5) -> Distribution:
        """
        from cos distribution at leading edge, to a const distribution at +- 1
        """

        def f(x):
            return x ** 2 / ((-2 + border) * border) if x < border else (2 * x - border)/(-2 + border)

        dist_values = np.linspace(0, 1, int(numpoints / 2) + 1)
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

    def make_symmetric_from_lower(self):
        lower = []
        for x in self.data:
            if x > 0:
                lower.append(x)
        lower = np.array(lower)
        upper = -lower
        new_dist = sorted(set(upper.tolist() + lower.tolist() + [0]))
        self.data = new_dist
