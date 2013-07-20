import numpy as np


def Depth(object):
    if isinstance(object, list) or isinstance(object, np.ndarray):
        return max([Depth(i) for i in object]) + 1
    else:
        return 1


def Type(object):
    """return type of a vector list: 2d-point (1), list of 2d-points (2), 3d-point (3), list of 3d-points (4)"""
    ##2d-point//listof2d-points//3d-point//listof3d-points
    ##2d-p: depth 1

    if Depth(object) == 2:
        if len(object) == 2:
            return 1
        elif len(object) == 3:
            return 3
        else:
            return 0
    elif Depth(object) == 3:
        if [Depth(i) for i in object] == [2 for i in object]:
            if [len(i) for i in object] == [2 for i in object]:
                return 2
            elif [len(i) for i in object] == [3 for i in object]:
                return 4
            else:
                return 0
        else:
            return 0
    else:
        return 0


def Norm(vector):
    return np.sqrt(np.dot(vector, vector))


def Normalize(vector):
    return vector / Norm(vector)


def Rotation_3D(angle, axis=[1, 0, 0]):
    """3D-Rotation Matrix for (angle[rad],[axis(x,y,z)])
    see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
    a = np.cos(angle / 2)
    (b,c,d) = -Normalize(axis) * np.sin(angle / 2)
    return np.array([[a**2+b**2-c**2-d**2,  2*(b*c - a*d),          2*(b*d + a*c)],
                     [2*(b*c + a*d),        a**2+c**2-b**2-d**2,    2*(c*d - a*b)],
                     [2*(b*d-a*c),          2*(c*d + a*b),          a**2 + d**2 - b**2 - c**2]])

def Rotation_3D_Wiki(angle,axis=[1,0,0]):

    #see http://en.wikipedia.org/wiki/Rotation_matrix#Rotation_matrix_from_axis_and_angle for reference.
    (x,y,z)=Normalize(axis)
