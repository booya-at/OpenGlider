import numpy as np

from openglider.utils import sign
from openglider.utils.cache import cached_property, HashedList
from openglider.vector.functions import norm, normalize, rangefrom, rotation_2d, cut
from openglider.utils.table import Table


class PolyLine(HashedList):
    def __init__(self, data, name=None):
        super(PolyLine, self).__init__(data, name)

    def __getitem__(self, ik):
        if isinstance(ik, int) and 0 <= ik < len(self):  # easiest case
            return self.data[ik]
        elif isinstance(ik, slice):  # example: list[1.2:5.5:1]
            values = self.get_positions(ik.start, ik.stop, ik.step)
            #print(values, ik.start, ik.stop, ik.step, step, start_round, stop_round)
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

    def get(self, start, stop):
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
            # Fasten up as well
            if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
                break
        return length + norm(self[second] - self[first])

    def get_segment_lengthes(self):
        lengths = []
        segments = self.get_segments()
        for s in segments:
            lengths.append(norm(s))

        return lengths

    def get_segments(self):
        segments = []
        for p1, p2 in zip(self.data[:-1], self.data[1:]):
            segments.append(p2 - p1)

        return segments

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


class PolyLine2D(PolyLine):
    def __add__(self, other):  # this is python default behaviour for lists
        if other.__class__ is self.__class__:
            if len(self.data) == 0:
                return other.copy()
            elif len(other.data) == 0:
                return self.copy()
            # elif all(self.data[-1] == other.data[0]):
            #     return self.__add__(other[1:])
            else:
                return self.__class__(np.append(self.data, other.data, axis=0), self.name)
        else:
            raise ValueError("cannot append: ", self.__class__, other.__class__)

    def __getitem__(self, ik):
        res = super(PolyLine2D, self).__getitem__(ik)
        if isinstance(ik, slice):
            return PolyLine2D(res.data)
        return res

    def cut(self, p1, p2, startpoint=0, extrapolate=False, cut_only_positive=False):
        """
        Iterate over all cuts with the line p1p2
        if extrapolate is true, cuts will be exceeding the lists length
        """
        startpoint = int(startpoint)
        for i in rangefrom(len(self)-1, startpoint):
            try:
                # (x,y), i, k
                pos, ik1, ik2 = cut(self[i], self[i+1], p1, p2)
                good_cut = 0 < ik1 <= 1 or ik1 == i == 0
                extrapolated_front = i == 0 and ik1 <= 0
                extrapolated_back = i == len(self)-2 and ik1 > 0
                extrapolated_cut = extrapolated_front or extrapolated_back

                if good_cut or extrapolate and extrapolated_cut:
                    if cut_only_positive and ik2 < 0:
                        continue
                    yield i+ik1, ik2
            except np.linalg.LinAlgError:
                continue

    def cut_with_polyline(self, pl, startpoint=0):
        for i, (p1, p2) in enumerate(zip(pl[:-1], pl[1:])):
            l = norm(p2-p1)
            for ik1, k2 in self.cut(p1, p2, startpoint, cut_only_positive=True):
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
                        self.data = np.concatenate([self.data[:i], [temp[0]], self.data[j+1:]])
                except np.linalg.linalg.LinAlgError:
                    continue

        return self

    @cached_property('self')
    def normvectors(self):   #RENAME: norm_point_vectors?
        """
        Return Normvectors to the List-Line, heading rhs
        this property returns a normal for every point,
        approximated by the 2 neighbour points (len(data) == len(normals))
        """
        rotate = lambda x: normalize(x).dot([[0, -1], [1, 0]])
        normvectors = [rotate(self.data[1] - self.data[0])]
        for j in range(1, len(self.data) - 1):
            normvectors.append(
                #rotate(normalize(self.data[j + 1] - self.data[j]) + normalize(self.data[j] - self.data[j - 1])))
                rotate(self.data[j + 1] - self.data[j - 1]))
        normvectors.append(rotate(self.data[-1] - self.data[-2]))
        return normvectors


    @cached_property('self')
    def tangents(self):
        tangents = []
        for p1, p2 in self.segments:
            tangents.append((p2 - p1) / norm(p2 - p1))
        return np.array(tangents)

    @cached_property('self')
    def norm_segment_vectors(self):
        """
        return all the normals based on the segments of the data:
        len(data) - 1 == len(normals)
        """
        rotate = lambda x: normalize(x).dot([[0, -1], [1, 0]])
        normvectors = []
        for p1, p2 in self.segments:
            normvectors.append(rotate(normalize(p2 - p1)))
        return np.array(normvectors)

    def get_normal(self, ik):
        """get normal-vector by ik-value"""
        normals = self.norm_segment_vectors
        if ik % 1 == 0:
            if int(ik) == len(normals):
                return normals[int(ik) - 1]
            elif int(ik) == 0:
                return normals[0]
            else:
                return (normals[int(ik) - 1] + normals[int(ik)]) / 2
        return normals[int(ik)]

    @property
    def segments(self):
        data = self.data
        segments = []
        for i in range(len(self) - 1):
            segments.append(data[i:i+2])
        return np.array(segments)

    def move(self, vector):
        """
        Move the whole line
        """
        assert len(vector) == 2
        #print(vector)
        self.data += vector[:]

        return self

    def add_stuff(self, amount):
        """
        Shift the whole line for a given amount (->Sewing allowance)
        """
        # cos(vectorangle(a,b)) = (a1 b1+a2 b2)/Sqrt[(a1^2+a2^2) (b1^2+b2^2)]
        newlist = []
        second = self.data[0]
        third = self.data[1]
        newlist.append(second + self.norm_segment_vectors[0] * amount)
        for i in range(1, len(self.data) - 1):
            first = second
            second = third
            third = self.data[i + 1]
            d1 = second - first
            d2 = third - second
            cosphi = d1.dot(d2) / np.sqrt(d1.dot(d1) * d2.dot(d2))
            coresize = 1e-8
            if cosphi > 0.9999 or norm(d1) < coresize or norm(d2) < coresize:
                newlist.append(second + self.normvectors[i] * amount / cosphi)
            elif cosphi < -0.9999: # this is true if the direction changes 180 degree
                n1 = self.norm_segment_vectors[i-1]
                n2 = self.norm_segment_vectors[i]
                newlist.append(second + self.norm_segment_vectors[i-1] * amount)
                newlist.append(second + self.norm_segment_vectors[i] * amount)
            else:
                n1 = self.norm_segment_vectors[i-1]
                n2 = self.norm_segment_vectors[i]
                sign = -1. + 2. * (d2.dot(n1) > 0)
                phi = np.arccos(n1.dot(n2))
                d1 = normalize(d1)
                ext_vec = n1 - sign * d1 * np.tan(phi / 2)
                newlist.append(second + ext_vec * amount)

                # newlist.append(cut(a, b, c, d)[0])
        newlist.append(third + self.norm_segment_vectors[-1] * amount)
        self.data = newlist

        return self

    def mirror(self, p1, p2):
        """
        Mirror against a line through p1 and p2
        """
        p1 = np.array(p1)
        p2 = np.array(p2)
        normvector = normalize(np.array(p1-p2).dot([[0, -1], [1, 0]]))
        self.data = [point - 2*normvector.dot(point-p1)*normvector for point in self.data]

        return self

    def rotate(self, angle, startpoint=None, radians=True):
        """
        Rotate counter-clockwise around a (non)given startpoint [rad]
        """
        if not radians:
            angle = np.pi*angle/180
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
        import svgwrite.container
        drawing = svgwrite.Drawing(size=[800, 800*height/width])

        drawing.viewbox(bbox[0][0]-border*width, -bbox[1][1]-border*height, width*(1+2*border), height*(1+2*border))
        g = svgwrite.container.Group()
        g.scale(1, -1)
        line = drawing.polyline(np.array(self.data, dtype=float),
                                style="stroke:black; vector-effect: non-scaling-stroke; fill: none;")
        g.add(line)
        drawing.add(g)

        return drawing.tostring()