import math
import numpy


def norm(vector):
    """
    Norm-Function for n-dimensional vectors
    """
    return numpy.sqrt(numpy.vdot(vector, vector))


def norm_squared(vector):
    """
    Norm_squared
    """
    return numpy.vdot(vector, vector)


def normalize(vector):
    """
    Normalize n-dimensional vectors
    """
    leng = norm_squared(vector)
    if leng > 0:
        return vector / norm(vector)
    raise ValueError("Cannot normalize a vector of length Zero")


def vector_angle(v1, v2):
    return math.atan2(v1[1], v1[0]) - math.atan2(v2[1], v2[0])


def rangefrom(maxl, startpoint=0):
    """
    yield iterative, similar to range() but surrounding a certain startpoint
    """
    j = 1
    if 0 <= startpoint < maxl:
        yield startpoint
    while startpoint - j >= 0 or startpoint + j < maxl:
        if startpoint + j < maxl:
            yield startpoint + j
        if maxl > startpoint - j >= 0:
            yield startpoint - j
        j += 1


def rotation_3d(angle, axis=None):
    """
    3D-Rotation Matrix for (angle[rad],[axis(x,y,z)])
    """
    if axis is None:
        axis = [1, 0, 0]
    # see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
    a = numpy.cos(angle / 2)
    (b, c, d) = -normalize(axis) * numpy.sin(angle / 2)
    return numpy.array([
        [a**2 + b**2 - c**2 - d**2, 2*(b*c - a*d),              2*(b*d + a*c)],
        [2*(b*c + a*d),             a**2 + c**2 - b**2 - d**2,  2 * (c*d - a*b)],
        [2*(b*d - a*c),             2*(c*d + a*b),              a**2 + d**2 - b**2 - c**2]
    ])


def rotation_2d(angle):
    """
    Return a 2D-Rotation-Matrix
    """
    return numpy.array([[numpy.cos(angle), numpy.sin(angle)], [-numpy.sin(angle), numpy.cos(angle)]])


def cut(p1, p2, p3, p4):
    """
    2D-Linear Cut; Solves the linear system: p1+k*(p2-p1)==p3+l*(p4-p3)
    Returns (point(x, y), k, l)
    """
    """ |p2x-p1x -(p4x-p3x)|*|k|==|p3x-p1x|"""
    """ |p2y-p1y -(p4y-p3y)|*|l|==|p3y-p1y|"""
    matrix = [[p2[0] - p1[0], p3[0] - p4[0]],
              [p2[1] - p1[1], p3[1] - p4[1]]]
    rhs = [p3[0] - p1[0], p3[1] - p1[1]]
    (k, l) = numpy.linalg.solve(matrix, rhs)
    return p1 + k * (p2 - p1), k, l

