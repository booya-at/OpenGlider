import numpy

from openglider.utils import sign
from openglider.utils.cache import cached_property, HashedList
from openglider.vector.functions import norm, normalize, rangefrom, rotation_2d, cut


class PolyLine(HashedList):
    def __init__(self, data, name=None):
        super(PolyLine, self).__init__(data, name)

    def __getitem__(self, ik):
        if isinstance(ik, int) and 0 <= ik < len(self):  # easiest case
            return self.data[ik]
        elif isinstance(ik, slice):  # example: list[1.2:5.5:1]
            values = self.get_positions(ik.start, ik.stop, ik.step)
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
        new = self.copy()
        new *= other
        return new

    def __imul__(self, other):
        """Scale self"""
        assert len(other) == 2
        self.scale(*other)
        return self

    def join(self, *other):
        self.data = numpy.concatenate([self.data] + list(other))
        return self

    def point(self, x):
        """List.point(x) is the same as List[x]"""
        return self[x]

    def last(self):
        return self[len(self) - 1]

    def get(self, start, stop):
        start2 = start - start % 1 + 1
        stop2 = stop - stop % 1
        data = self.data[start2:stop2]
        return numpy.concatenate([[self[start]], data, [self[stop]]])

    def get_positions(self, start=0, stop=None, step=None):
        stop = stop if stop is not None else len(self)-1
        start = start if start is not None else 0
        if step is not None and step < 0:
            start, stop = stop, start
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
                self.data = numpy.concatenate([self[:index], self[index+1:]])
            else:
                index += 1

        return self

    def extend(self, start, length):
        """
        Move from a starting point for a given length in direction of the line
        """
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
            # Fasten up aswell
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
        return length + norm(self[second] - self[first])

    def scale(self, x, y=None):
        if y is None:
            y = x
        self.data *= [x, y]
        return self


class PolyLine2D(PolyLine):
    def __add__(self, other):  # this is python default behaviour for lists
        if other.__class__ is self.__class__:
            if len(self.data) == 0:
                return other.copy()
            elif len(other.data) == 0:
                return self.copy()
            else:
                return self.__class__(numpy.append(self.data, other.data, axis=0), self.name)
        else:
            raise ValueError("cannot append: ", self.__class__, other.__class__)

    def new_cut(self, p1, p2, startpoint=0, extrapolate=False, cut_only_positive=False):
        """
        Iterate over all cuts with the line p1p2
        if extrapolate is true, cuts will be exceeding the lists length
        """
        startpoint = int(startpoint)
        for i in rangefrom(len(self)-1, startpoint):
            try:
                # (x,y), i, k
                thacut = cut(self[i], self[i+1], p1, p2)
                good_cut = 0 < thacut[1] <= 1 or thacut[1] == i == 0
                extrapolated_front = i == 0 and thacut[1] <= 0
                extrapolated_back = i == len(self)-2 and thacut[1] > 0
                extrapolated_cut = extrapolated_front or extrapolated_back

                if good_cut or extrapolate and extrapolated_cut:
                    if cut_only_positive and thacut[2] < 0:
                        continue
                    yield i+thacut[1]
            except numpy.linalg.LinAlgError:
                continue

    def cut_with_polyline(self, pl, startpoint=0):
        for i, (p1, p2) in enumerate(zip(pl[:-1], pl[1:])):
            l = norm(p2-p1)
            for ik1 in self.new_cut(p1, p2, startpoint, cut_only_positive=True):
                ik2 = i + (norm(self[ik1] - p1) / l)
                yield ik1, ik2

    def check(self):  # TODO: IMPROVE (len = len(self.data), len-=,...)
        """
        Check for mistakes in the array, such as for the moment: self-cuttings,..
        """
        super(PolyLine2D, self).check()
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

        return self

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

        return self

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

        return self

    def mirror(self, p1, p2):
        """
        Mirror against a line through p1 and p2
        """
        p1 = numpy.array(p1)
        p2 = numpy.array(p2)
        normvector = normalize(numpy.array(p1-p2).dot([[0, -1], [1, 0]]))
        self.data = [point - 2*normvector.dot(point-p1)*normvector for point in self.data]

        return self

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

        return self

    def get_bbox(self):
        if not self:
            return [[0,0], [0,0]]
        return [
            [min([p[0] for p in self]), min([p[1] for p in self])],
            [max([p[0] for p in self]), max([p[1] for p in self])],
        ]

    def _repr_svg_(self):
        border = 0.1
        bbox = self.get_bbox()
        width = bbox[1][0] - bbox[0][0]
        height = bbox[1][1] - bbox[0][1]

        import svgwrite
        drawing = svgwrite.Drawing(size=[800, 800*height/width])

        drawing.viewbox(bbox[0][0]-border*width, bbox[0][1]-border*height, width*(1+2*border), height*(1+2*border))
        drawing.add(drawing.polyline(self.data, style="stroke:black; vector-effect: non-scaling-stroke; fill: none;"))

        return drawing.tostring()