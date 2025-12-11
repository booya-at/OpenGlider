import numpy as np
from .functions import normalize


class Transformation(object):
    """
    Transformation represented by a 4x4 matrix. This includes transformation + translation.
    """

    def __init__(self, mat):
        # mat is a 4 x 4 matrix
        assert len(mat) == len(mat.T) == 4
        self.mat = np.array(mat)

    def __call__(self, vec):
        vec = np.array(vec)
        assert len(vec.shape) == 1
        vec = np.array([vec])
        return self.apply(vec)[0]

    def apply(self, vec):
        if len(vec[0]) == 2:
            return vec.dot(self.mat[:2, :2]) + self.mat[-1, :2]
        elif len(vec[0]) == 3:
            return vec.dot(self.mat[:3, :3]) + self.mat[-1, :3]
        else:
            return vec.dot(self.mat[:4, :4])

    def dot(self, other):
        return Transformation(self.mat.dot(other.mat))

    def __mul__(self, other):
        return Transformation(self.mat.dot(other.mat))


class Rotation(Transformation):
    def __init__(self, angle=0.0, axis=None):
        # see http://en.wikipedia.org/wiki/SO%284%29#The_Euler.E2.80.93Rodrigues_formula_for_3D_rotations"""
        if axis is None:
            axis = np.array([0.0, 0.0, 1.0])
        assert len(axis) == 3
        a = np.cos(angle / 2)
        (b, c, d) = -normalize(axis) * np.sin(angle / 2)
        mat = np.array(
            [
                [
                    a**2 + b**2 - c**2 - d**2,
                    2 * (b * c - a * d),
                    2 * (b * d + a * c),
                    0.0,
                ],
                [
                    2 * (b * c + a * d),
                    a**2 + c**2 - b**2 - d**2,
                    2 * (c * d - a * b),
                    0.0,
                ],
                [
                    2 * (b * d - a * c),
                    2 * (c * d + a * b),
                    a**2 + d**2 - b**2 - c**2,
                    0.0,
                ],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        super(Rotation, self).__init__(mat)


class Reflection(Transformation):
    def __init__(self, axis=None):
        if axis is None:
            axis = np.array([0.0, 1.0, 0.0])
        assert len(axis) == 3
        x, y, z = normalize(axis)
        mat = np.array(
            [
                [1 - 2 * x**2, -2 * x * y, -2 * x * z, 0.0],
                [-2 * x * y, 1 - 2 * y**2, -2 * y * z, 0.0],
                [-2 * x * z, -2 * y * z, 1 - 2 * z**2, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        super(Reflection, self).__init__(mat)


class Scale(Transformation):
    def __init__(self, scale_values=None):
        if scale_values is None:
            scale_values = np.ones(3)
        elif isinstance(scale_values, (int, float)):
            scale_values = np.ones(3) * scale_values
        _scale_values = np.ones(4)
        _scale_values[: len(scale_values)] = scale_values
        mat = np.diag(_scale_values)
        super(Scale, self).__init__(mat)


class Translation(Transformation):
    def __init__(self, vec=None):
        if vec is None:
            vec = np.zeros(3)
        mat = np.eye(4)
        mat[-1, : len(vec)] = vec
        super(Translation, self).__init__(mat)
