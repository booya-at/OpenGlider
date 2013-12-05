import numpy as np
from openglider.Utils import sign


def depth(arg):
    if isinstance(arg, list) or isinstance(arg, np.ndarray):
        return max([depth(i) for i in arg]) + 1
    else:
        return 1


def arrtype(arg):
    """return type of a vector list: 2d-point (1), list of 2d-points (2), 3d-point (3), list of 3d-points (4)"""
    ##2d-point//argof2d-points//3d-point//argof3d-points
    ##2d-p: depth 1
    ##equivalent numpy.rank?

    ######Room for improvement here!

    if depth(arg) == 2:
        if len(arg) == 2:
            return 1
        elif len(arg) == 3:
            return 3
        else:
            return 0
    elif depth(arg) == 3:
        if [depth(i) for i in arg] == [2 for i in arg]:
            if [len(i) for i in arg] == [2 for i in arg]:
                return 2
            elif [len(i) for i in arg] == [3 for i in arg]:
                return 4
            else:
                return 0
        else:
            return 0
    else:
        return 0


def norm(vector):
    return np.sqrt(np.vdot(vector, vector))


def normalize(vector):
    return vector / norm(vector)


def rangefrom(maxl, startpoint=0):
    """Iterative, similar to range() but surrounding a certain startpoint"""
    j = 1
    if 0 <= startpoint <= maxl:
        yield startpoint
    while startpoint-j >= 0 or startpoint+j <= maxl:
        if startpoint+j <= maxl:
            yield startpoint+j
        if maxl >= startpoint-j >= 0:
            yield startpoint-j
        j += 1

def rotation_3d(angle, axis=[1, 0, 0]):
    """3D-Rotation Matrix for (angle[rad],[axis(x,y,z)])"""
    # see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
    a = np.cos(angle / 2)
    (b, c, d) = -normalize(axis) * np.sin(angle / 2)
    return np.array([[a ** 2 + b ** 2 - c ** 2 - d ** 2, 2 * (b * c - a * d), 2 * (b * d + a * c)],
                     [2 * (b * c + a * d), a ** 2 + c ** 2 - b ** 2 - d ** 2, 2 * (c * d - a * b)],
                     [2 * (b * d - a * c), 2 * (c * d + a * b), a ** 2 + d ** 2 - b ** 2 - c ** 2]])

#def Rotation_3D_Wiki(angle,axis=[1,0,0]):
#see http://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle for reference.
#    (x,y,z)=normalize(axis)


def cut(p1, p2, p3, p4):
    """2D-Linear Cut; Returns (pointxy, k, l); Solves the linear system: p1+k*(p2-p1)==p3+l*(p4-p3)"""
    """ |p2x-p1x -(p4x-p3x)|*|k|==|p3x-p1x|"""
    """ |p2y-p1y -(p4y-p3y)|*|l|==|p3y-p1y|"""
    matrix = [[p2[0]-p1[0], p3[0]-p4[0]],
              [p2[1]-p1[1], p3[1]-p4[1]]]
    rhs = [p3[0]-p1[0], p3[1]-p1[1]]
    (k, l) = np.linalg.solve(matrix, rhs)
    return p1 + k*(p2-p1), k, l


class Vectorlist(object):
    def __init__(self, data=[], name="Vector List object"):
        #if arrtype(data) == 2 or arrtype(data) == 4:
        self.data = np.array(data)
        self.name = name

    def __repr__(self):
        return self.data.__str__()

    def __str__(self):
        return self.name

    def __getitem__(self, ik):
        if ik < 0:
            k = ik
            i = 0
        else:
            i = min(int(ik), len(self.data)-2)  # Upper Limit for i
            # case1: 0<ik<len -> k=ik%1;
            # case2: ik>len(self.data) -> k += difference
            k = ik % 1 + max(0, int(ik) - len(self.data)+2)
        return self.point(i, k)

    def __len__(self):
        return len(self.data)

    def copy(self):
        return self.__class__(self.data.copy(), self.name+"_copy")

    def point(self, i, k=0):
        if i > len(self.data) or i < 0 or not isinstance(i, int):
            raise ValueError("invalid data for listpoint")
        return self.data[i] + k * (self.data[i + 1] - self.data[i])

    def extend(self, start, length):
        if length == 0:
            return start
        direction = sign(length)
        length = abs(length)
        next_value = start - start % 1 + (direction > 0)
        difference = norm(self[start]-self[next_value])
        length -= difference
        #
        while length > 0:
            #if (next_value > len(self) and direction > 0) or (next_value < 0 and direction < 0):
            #    break
            start = next_value
            next_value += direction
            difference = norm(self[next_value]-self[start])
            length -= difference
        # Length is smaller than zero
        length = length
        return next_value + direction * length * abs(next_value-start) / difference


    def extend2(self, start, length):
        direction = sign(length)
        length = abs(length)
        #print("new array:")
        #print("length: %s, start: %s, direction: %s, array length: %s" % (length, start, direction, len(self.data)))
        # TODO: If we should stay in the same cell we increment here:
        next_value = int(start - start % 1 + (direction > 0))
        # TODO: This is just a quick fix:
        difference = norm(self[next_value]-self[start])
        if (length - difference) < 0:
            skip = True
        else:
            skip = False
        #length -= difference

        while length > 0 and not skip:
            #next_value = start + (direction > 0) - start % 1
            #if start % 1:  # start is not an integer yet
            #    next_value = int(start - start % 1 + (direction > 0))
            #else:  # start is an integer
            #    next_value = start + direction
            #print("new passtrough:")
            #clamp it between zero and the last value
            next_value = max(0, min(len(self.data) - 1, next_value))
            #the difference between the start and next_value point
            difference = norm(self[start] - self[next_value])
            print("length: %s, difference: %s, start: %s, next_value: %s" % (length, difference, start, next_value))
            if (next_value == 0 and direction < 0) or (next_value == len(self.data) - 1 and direction > 0):
                # we are on the end of the points, extrapolate the rest
                #return start + direction * (start-next) * length / difference
                # Difference = norm(last-forelast)
                print("break now!, length: %s" % difference)
                break
            length -= difference
            #we may fall out now, set difference right
            #difference /= abs(start - next_value)
            start = next_value
            # TODO: AND HERE!
            next_value = start + direction
            #print("end of while: %s" % length)
        #print("finished while")
        #print("got difference from: %s and %s" % (next_value, (next_value - direction)))
        #print("start: %s, direction: %s, length: %s, difference: %s" % (start, direction, length, difference))
        return start + direction * abs(start - next_value) * length / difference

    def extend_old_new(self, start, length):

        direction = sign(length)
        p1 = self[start]
        next_value = start - (start % 1) + (direction > 0)
        p2 = self[next_value]
        diff = norm(p2-p1)

        while diff < length and 0 < next_value < len(self):
            next_value += direction
            p1 = p2
            p2 = self[next_value]
            temp = norm(p2 - p1)
            diff += temp

        next_value -= (direction > 0)
        i = start - (start % 1)
        if next_value == i:
            dl = norm(p1 - self[i])
            return (start - i) * (dl + length) / dl
        else:
            return i + (diff - length) / temp - (length > 0)


    def extend_old(self, start, length):
        """Extend the List at a given Point (i,k) by the given Length and return NEW (i,k)"""
        (i, k) = start
        _dir = sign(length)
        _len = abs(length)

        p1 = self.point(i, k)

        if _dir == 1:
            (inew, knew) = (i + 1, 0)
        else:
            (inew, knew) = (i, 0)

        p2 = self.data[inew]
        diff = norm(p2 - p1)

        while diff < _len and len(self.data) - 1 > inew > 0:
            inew += _dir
            p1 = p2
            p2 = self.data[inew]
            temp = norm(p2 - p1)
            diff += temp
            # so here we are now, one too far or at the end//beginning of the list

        inew -= (_dir + 1) / 2  # only for positive direction
        if inew == i:                       # New Point is in the same 'cell'
            d1 = norm(p1 - self.data[i])
            knew = k * (d1 + length) / d1
        else:                               # something between or further than the beginning/end
            knew = (diff - _len)/ temp
            if _dir == 1:
                knew = 1 - knew

        return inew, knew

    def get_length_old(self, p1a=(0, 0), p2a=(-2, 1)):
        (i1, k1) = p1a
        (i2, k2) = p2a
        length = 0
        if sign(i2) is -1:
            i2 += len(self.data)
            #print(i2)

        p1 = self.point(i1, k1)
        p2 = p1

        while i1 < i2:
            i1 += 1
            p1 = p2
            p2 = self.data[i1]
            length += norm(p2 - p1)

        p1 = p2
        p2 = self.point(i2, k2)
        length += norm(p2 - p1)
        return length

    def get_length(self, first, second):
        direction = sign(float(second-first))
        temp = second-first
        dir2=sign(temp)
        length = 0
        next_value = int(first - first % 1 + (direction > 0))
        while next_value * direction < second * direction:
            #print("zjuhui")
            length += norm(self[next_value] - self[first])
            first = next_value
            next_value += direction
            # TODO: if first < 0, > len(self.data): make shorteraaa
        return length + norm(self[second] - self[first])




class Vectorlist2D(Vectorlist):
    def cut(self, p1, p2, startpoint=0):
        for i in rangefrom(len(self.data)-2, startpoint):
            try:  # in case we have parallell lines we dont get a result here, so we continue with i raised...
                thacut = cut(self.data[i], self.data[i+1], p1, p2)
            except np.linalg.linalg.LinAlgError:
                continue
            if 0 < thacut[1] <= 1.:
                return thacut[0], (i, thacut[1])
        # Nothing found yet? check start and end of line
        thacut = []
        for i in [1, -1]:
            #####change the sorting to fit absolute length, not diff-parameter
            try:
                temp = [cut(self.data[i-1], self.data[i], p1, p2)]
                if sign(temp[1]) == sign(i):
                    thacut += temp
            except np.linalg.linalg.LinAlgError:
                continue
        thacut.sort(key=lambda x: abs(x[1]))
        return thacut[0]

    def check(self):
        """Check for mistakes in the array, such as for the moment: self-cuttings,"""
        for i in range(len(self.data)-2):
            for j in range(len(self.data)-2, i):
                temp = cut(self.data[i], self.data[i+1], self.data[j], self.data[j+1])
                if temp[1] <= 1. and temp[2] <= 1.:
                    self.data = np.   self.data[:i], temp[0], self.data[j+1:]

    def normvectors(self):
        rotate = lambda x: normalize(x).dot([[0, -1], [1, 0]])
        vectors = [rotate(self.data[1]-self.data[0])]
        for j in range(1, len(self.data)-2):
            vectors.append(rotate(normalize(self.data[j+1]-self.data[j])+normalize(self.data[j]-self.data[j-1])))
        vectors.append(rotate(self.data[-1]-self.data[-2]))
        return np.array(vectors)
