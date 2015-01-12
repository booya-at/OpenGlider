import numpy
from openglider.utils import sign
from openglider.utils.cache import cached_property, HashedList
from openglider.vector.functions import norm, normalize, rangefrom, rotation_2d, \
    cut


class PolyLine(HashedList):
    def __init__(self, data, name=None):
        super(PolyLine, self).__init__(data, name)

    def __getitem__(self, ik):
        if isinstance(ik, int) and 0 <= ik < len(self):  # easiest case
            return self.data[ik]
        elif isinstance(ik, slice):  # example: list[1.2:5.5:1]
            start = ik.start if ik.start is not None else 0
            stop = ik.stop if ik.stop is not None else len(self)-1
            if ik.step is not None and ik.step < 0:
                start, stop = stop, start
            step = sign(stop - start)
            if step > 0:
                start_round = max(int(start) + 1, 0)
                stop_round = min(int(stop) + (1 if stop % 1 > 0 else 0), len(self) - 1)
            else:
                start_round = min(int(start) - (0 if start % 1 > 0 else 1), len(self) - 1)
                stop_round = max(int(stop), 0)
            values = [start] + range(start_round, stop_round, step) + [stop]
            #print(values, ik.start, ik.stop, ik.step, step, start_round, stop_round)
            return self.__class__([self[i] for i in values])
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
        assert len(other) == 2
        new = self.copy()
        new.scale(*other)
        return new

    def __imul__(self, other):
        """Scale self"""
        assert len(other) == 2
        self.scale(*other)

    def point(self, x):
        """List.point(x) is the same as List[x]"""
        return self[x]

    def get(self, start, stop):
        start2 = start - start % 1 + 1
        stop2 = stop - stop % 1
        data = self.data[start2:stop2]
        return numpy.concatenate([[self[start]], data, [self[stop]]])

    def extend(self, start, length):
        if length == 0:
            return start
        direction = sign(length)
        length = abs(length)
        next_value = start - start % 1 + (direction > 0)
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
        length = length
        return next_value + direction * length * abs(next_value - start) / difference

    def get_length(self, first=0, second=None):
        """
        Get the (normative) Length of a Part of the Vectorlist.
        """
        if not second:
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
            # Fasten up aswell
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
        return length + norm(self[second] - self[first])

    def scale(self, x, y=None):
        if y is None:
            y = x
        self.data *= [x, y]


class PolyLine2D(PolyLine):
    def __init__(self, data, name=None):
        self._normvectors = None
        super(PolyLine2D, self).__init__(data, name)

    def __add__(self, other):  # this is python default behaviour for lists
        if other.__class__ is self.__class__:
            if self.data is not None:
                return self.__class__(numpy.append(self.data, other.data, axis=0), self.name)
            else:
                return other.copy()
        else:
            raise ValueError("cannot append: ", self.__class__, other.__class__)

    def new_cut(self, p1, p2, startpoint=0, extrapolate=False):
        """
        Iterate over all cuts with the line p1p2
        if extrapolate is true, cuts will be exceeding the lists length
        """
        for i in rangefrom(len(self)-2, startpoint):
            try:
                thacut = cut(self[i], self[i+1], p1, p2)
                good_cut = 0 < thacut[1] <= 1 or thacut[1] == i == 0
                extrapolated_cut = i == 0 and thacut[1] <= 0 or \
                                   i == len(self)-1 and thacut[1] > 0

                if good_cut or extrapolate and extrapolated_cut:
                    yield i+thacut[1]
            except numpy.linalg.LinAlgError:
                continue

    # TODO: make a iterator
    def cut(self, p1, p2, startpoint=0, break_if_found=True,
            cut_only_positive=False, cut_only_in_between=False):
        """
        Cut with two points given, returns (point, position_in_list, k [*(p2-p1)])
        """
        startpoint = int(startpoint)
        cutlist = []

        for i in rangefrom(len(self) - 2, startpoint):
            try:
                thacut = cut(self[i], self[i + 1], p1, p2)  # point, i, k
            except numpy.linalg.linalg.LinAlgError:
                continue
            if (0 <= thacut[1] < 1 and
                    (not cut_only_positive or thacut[2] >= 0) and
                    (not cut_only_in_between or thacut[2] <= 1.)):
                cutlist.append((thacut[0], i + thacut[1], thacut[2]))
                if break_if_found:
                    return cutlist[0]

        if len(cutlist) > 0:
            return cutlist

        # Nothing found yet? Shit, so, check start and end of line
        # Beginning
        try:
            temp = cut(self[0], self[1], p1, p2)
            if temp[1] <= 0:
                cutlist.append([temp[0], temp[1], norm(self[0] - self[1]) * temp[1]])
        except numpy.linalg.linalg.LinAlgError:
            pass
        # End
        try:
            i = len(self) - 1
            temp = cut(self[i], self[i + 1], p1, p2)
            if temp[1] > 0:
                cutlist.append([temp[0], i + temp[1], norm(self[i] - self[i + 1]) * temp[1]])
        except numpy.linalg.linalg.LinAlgError:
            pass

        if len(cutlist) > 0:
            # sort by distance
            cutlist.sort(key=lambda x: x[2]**2)
            #print(cutlist[0])
            return cutlist[0][0:2]
        else:
            #graphics([Line(self.data), Line([p1,p2])])  # DEBUG
            raise ArithmeticError("no cuts discovered for p1:" + str(p1) + " p2:" + str(p2) + str(self[0]))
                                  #str(cut(self[0], self[1], p1, p2)))

    def check(self):  # TODO: IMPROVE (len = len(self.data), len-=,...)
        """
        Check for mistakes in the array, such as for the moment: self-cuttings,..
        """
        for i in range(len(self.data) - 3):
            if i > len(self.data) - 4:
                break
            for j in range(i + 2, len(self.data) - 2):
                if j > len(self.data) - 3:
                    break
                try:
                    temp = cut(self.data[i], self.data[i + 1], self.data[j], self.data[j + 1])
                    if 0 < temp[1] < 1. and 0 < temp[2] < 1.:
                        #self.data = self.data[:i] + [temp[0]] + self.data[j + 1:]
                        self.data = numpy.concatenate([self.data[:i], [temp[0]], self.data[j+1:]])
                except numpy.linalg.linalg.LinAlgError:
                    continue

    @cached_property('self')
    def normvectors(self):
        """
        Return Normvectors to the List-Line, heading rhs
        """
        rotate = lambda x: normalize(x).dot([[0, -1], [1, 0]])
        normvectors = [rotate(self.data[1] - self.data[0])]
        for j in range(1, len(self.data) - 1):
            normvectors.append(
                #rotate(normalize(self.data[j + 1] - self.data[j]) + normalize(self.data[j] - self.data[j - 1])))
                rotate(self.data[j + 1] - self.data[j - 1]))
        normvectors.append(rotate(self.data[-1] - self.data[-2]))
        return normvectors

    def move(self, vector):
        """
        Move the whole line
        """
        assert len(vector) == 2
        self.data += vector

    def add_stuff(self, amount):
        """
        Shift the whole line for a given amount (->Sewing allowance)
        """
        # cos(vectorangle(a,b)) = (a1 b1+a2 b2)/Sqrt[(a1^2+a2^2) (b1^2+b2^2)]
        newlist = []
        second = self.data[0]
        third = self.data[1]
        newlist.append(second + self.normvectors[0] * amount)
        i = 0
        for i in range(1, len(self.data) - 1):
            first = second
            second = third
            third = self.data[i + 1]
            d1 = third - second
            d2 = second - first
            cosphi = d1.dot(d2) / numpy.sqrt(d1.dot(d1) * d2.dot(d2))
            if cosphi > 0.9999:
                newlist.append(second + self.normvectors[i] * amount / cosphi)
            else:
                a = first+self.normvectors[i-1]*amount
                b = second+self.normvectors[i]*amount
                c = third + self.normvectors[i+1]*amount
                newlist.append(cut(a, b, b, c)[0])
        newlist.append(third + self.normvectors[i + 1] * amount)
        self.data = newlist

    def mirror(self, p1, p2):
        """
        Mirror against a line through p1 and p2
        """
        normvector = normalize(numpy.array(p1-p2).dot([[0, -1], [1, 0]]))
        self.data = [point - 2*normvector.dot(point-p1)*normvector for point in self.data]

    def rotate(self, angle, startpoint=None):
        """
        Rotate counter-clockwise around a (non)given startpoint [rad]
        """
        rotation_matrix = rotation_2d(angle)
        new_data = []
        for point in self.data:
            if startpoint is not None:
                new_data.append(startpoint + rotation_matrix.dot(point - startpoint))
            else:
                new_data.append(rotation_matrix.dot(point))
        self.data = new_data