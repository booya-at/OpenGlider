import numpy as np

from openglider.utils import sign
from openglider.utils.cache import cached_property, HashedList
from openglider.vector.functions import norm, normalize, rangefrom, \
                                        rotation_2d, cut, radius_from_3points, \
                                        curvature_from_3points
from openglider.utils.table import Table


class PolyLine(HashedList):
    def __init__(self, data, name=None):
        super(PolyLine, self).__init__(data, name)

    def __getitem__(self, ik):
        if isinstance(ik, int) and 0 <= ik < len(self):  # easiest case
            return self.data[ik]
        elif isinstance(ik, slice):  # example: list[1.2:5.5:1]
            values = self.get_positions(ik.start, ik.stop, ik.step)
            return PolyLine([self[i] for i in values])
        else:
            if ik < 0:
                k = ik
                i = 0
            else:
                i = min(int(ik), len(self.data) - 2)  # Upper Limit for i
                # case1: 0<ik<len -> k=ik%1;
                # case2: ik>len(self.data) -> k += difference
                k = ik % 1 + max(0, int(ik) - len(self.data) + 2)
            return self.data[i] + k * (self.data[i + 1] - self.data[i])

    def __mul__(self, other):
        """Scale"""
        new = self.copy()
        new *= other
        return new

    def __imul__(self, other):
        """Scale self"""
        try:
            scale = float(other)
            self.scale(scale)
        except TypeError:
            self.scale(*other)

        return self

    def add(self, other):
        new = self.copy()
        new.data += other.data
        return new

    def get_table(self):
        table = Table()

        for i, p in enumerate(self):
            for j, coord in enumerate(p):
                table.set_value(j, i, coord)

        return table

    def join(self, *other):
        self.data = np.concatenate([self.data] + list(other))
        return self

    def point(self, x):
        """List.point(x) is the same as List[x]"""
        return self[x]

    def last(self):
        return self[len(self) - 1]

    def get(self, start, stop=None):
        if stop is None:
            return self[start]
        start2 = int(start - start % 1 + 1)
        stop2 = int(stop - stop % 1)
        data = self.data[start2:stop2]
        return np.concatenate([[self[start]], data, [self[stop]]])

    def get_positions(self, start=0, stop=None, step=None):
        stop = stop if stop is not None else len(self)-1
        start = start if start is not None else 0
        if step is not None and step < 0:
            start, stop = stop, start

        if start == stop:
            return [start]

        step = sign(stop - start)
        if step > 0:
            start_round = max(int(start) + 1, 0)
            stop_round = min(int(stop) + (1 if stop % 1 > 0 else 0), len(self) - 1)
        else:
            start_round = min(int(start) - (0 if start % 1 > 0 else 1), len(self) - 1)
            stop_round = max(int(stop), 0)
        values = [start] + list(range(start_round, stop_round, step)) + [stop]
        return values


    def check(self):
        # remove zero-length segments
        index = 0
        while index < len(self)-1:
            if norm(self[index+1] - self[index]) < 0.0000001:
                self.data = np.concatenate([self[:index], self[index+1:]])
            else:
                index += 1

        return self

    def walk(self, start, length):
        """
        Move from a starting point for a given length in direction of the line
        TODO: rename -> walk(start, distance)
        """
        if length == 0:
            return start
        direction = sign(length)
        length = abs(length)
        next_value = start - start % 1 + (direction > 0)
        if abs(start-next_value) < 1e-5:
            next_value += direction
        difference = norm(self[start] - self[next_value])
        length -= difference
        #
        while length > 0:
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
            start = next_value
            next_value += direction
            difference = norm(self[next_value] - self[start])
            length -= difference
            # Length is smaller than zero
            
        return next_value + direction * length * abs(next_value - start) / difference

    def resample(self, num_points):
        """
        redistribute line segments to be of "same" length.
        That means to start from 0 and then move length/(num_points-1)
        """
        length = self.get_length()
        ik = 0
        distance = length/(num_points-1)
        data = [self[0]]
        for i in range(1, num_points-1):
            ik = self.walk(ik, distance)
            data.append(self[ik])

        data.append(self[len(self)-1])

        return self.__class__(data)

    def get_length(self, first=0, second=None):
        """
        Get the (normative) Length of a Part of the Vectorlist.
        """
        if second is None:
            second = len(self) - 1
        direction = sign(float(second - first))
        length = 0
        next_value = int(first - first % 1 + (direction > 0))
        # Just to fasten up
        if next_value > len(self) and direction < 0:
            next_value = len(self)
        elif next_value < 0 < direction:
            next_value = 0
        while next_value * direction < second * direction:
            length += norm(self[next_value] - self[first])
            first = next_value
            next_value += direction
            # Fasten up as well
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
        return length + norm(self[second] - self[first])

    def get_segment_lengthes(self) -> np.ndarray:
        return np.linalg.norm(self.get_segments(), axis=1)

    def get_segments(self):
        return self.data[1:] - self.data[:-1]

    def get_length_parameter(self, scale=0):
        """
        returns length porpotional parameter value
        scale ==  1: [0 , l]
        scale ==  0: [0 , 1]
        scale == -1: [-1, 1]
        """
        diff = self.get_segment_lengthes()
        length = np.array([0] + np.cumsum(diff).tolist())
        if scale in [0, -1]:
            length /= max(length)
            if scale == -1:
                length = length * (-2) + 1
        return length

    def scale(self, x, y=None):
        if y is None:
            y = x
        self.data *= [x, y]
        return self

    def cutByPlane(self, point_vector, normal_vector):
        """
        Get all cutting positions of the polyline and a plane
        """
        cut_list = []
        p = point_vector
        n = normal_vector
        lines = np.array([self._data[:-1], self._data[1:]]).T
        for line in lines:
            direction = line[1] - line[0]
            _lamda = n.dot(p - line[0]) / n.dot(direction)
            if (_lamda >= 0 and _lamda < 1):
                cut_list.append(line[0] + _lamda * direction)
        return cut_list

    @property
    def curvature_radius(self):
        data = self.data
        p1 = data[:-2]
        p2 = data[1:-1]
        p3 = data[2:]
        return radius_from_3points(p1, p2, p3)

    @property
    def curvature(self):
        data = self.data
        p1 = data[:-2]
        p2 = data[1:-1]
        p3 = data[2:]
        return curvature_from_3points(p1, p2, p3)
    
    @property
    def is_closed(self):
        for x1, x2 in zip(self.data[0], self.data[-1]):
            if x1 != x2:
                return False
        
        return True
    
    def close(self):
        """
        Close the ends of the polyline
        """
        if not self.is_closed:
            self.data = np.append(self.data, [self.data[0]], 0)
        
        return self
