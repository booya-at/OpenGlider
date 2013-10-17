import numpy as np
from Utils import sign


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
    return np.sqrt(np.dot(vector, vector))


def normalize(vector):
    return vector / norm(vector)

def rangefrom(maxl, startpoint=0):
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
    return (p1 + k*(p2-p1), k, l)


class Vectorlist(object):
    def __init__(self, data=[], name="Vector List object"):
        if arrtype(data) == 2 or arrtype(data) == 4:
            self.data = np.array(data)
            self.name = name

    def __repr__(self):
        return self.data.__str__()

    def __str__(self):
        return self.name

    def copy(self):
        return self.__class__(self.data.copy(), self.name+"_copy")

    def point(self, _ik, _k=0):
        try:
            (i, k) = _ik
        except TypeError:
            (i, k) = (_ik, _k)
        if i > len(self.data) or i < 0 or not isinstance(i, int):
            raise "invalid data for listpoint"
        return self.data[i] + k * (self.data[i + 1] - self.data[i])

    def extend(self, ding, length):
        """Extend the List at a given Point (i,k) by the given Length and return NEW (i,k)"""
        (i, k) = ding
        _dir = sign(length)
        _len = abs(length)

        p1 = self.point(i, k)

        if _dir == 1:
            (inew, knew) = (i + 1, 0)
        else:
            (inew, knew) = (i, 0)
        p2 = self.data[inew]
        diff = np.linalg.norm(p2 - p1)
        while diff < _len and len(self.data) - 1 > inew > 0:
            inew = inew + _dir
            p1 = p2
            p2 = self.data[inew]
            temp = np.linalg.norm(p2 - p1)
            diff += temp
            #we are now one too far or at the end//beginning of the list

        inew -= (_dir + 1) / 2  # only for positive direction
        if inew == i:  # New Point is in the same 'cell'
            d1 = np.linalg.norm(p1 - self.data[i])
            knew = k / d1 * (d1 + length)
        else:
            knew = (diff - _len) / temp  #
            if _dir == 1: knew = 1 - knew

        return inew, knew

    def get_length(self, p1=(0, 0), p2=(-2, 1)):
        (i1, k1) = p1
        (i2, k2) = p2
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
            length += np.linalg.norm(p2 - p1)

        p2 = self.point(i2, k2)
        length += np.linalg.norm(p2 - p1)
        return length


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
        vectors = np.array([rotate(self.data[1]-self.data[0])])
        for j in range(1, len(self.data)-2):
            vectors.append(rotate(normalize(self.data[j+1]-self.data[j])+normalize(self.data[j]-self.data[j-1])))
        vectors.append(rotate(self.data[-1]-self.data[-2]))
        return vectors
