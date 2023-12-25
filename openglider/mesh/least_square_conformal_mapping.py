# LSCM from
# Least Squares Conformal Maps for Automatic Texture Atlas Generation
# Bruno Levy
# Sylvain Petitjean
# Nicolas Ray
# Jerome Maillot
# ISA (Inria Lorraine and CNRS), France

from __future__ import division

import numpy as np
from numpy.linalg import norm

np.set_printoptions(3, suppress=True)


class LSCM(object):
    def __init__(self, vertices, triangles):
        self.vertices = np.array(vertices)  # n x 3
        self.triangles = np.array(triangles)  # m x 3
        self.areas = []
        self._set_areas()  # m

    def run(self):
        M = self.complex_M
        M_r = np.real(M)
        M_i = np.imag(M)
        M_r_f = M_r[:, 2:]  # the first two x_pos are fixed
        M_i_f = M_i[:, 2:]  # the first two y_pos are fixed
        M_r_p = M_r[:, :2]
        M_i_p = M_i[:, :2]
        M = np.bmat([[M_r_f, -M_i_f], [M_i_f, M_r_f]])
        M_rhs = np.bmat([[M_r_p, -M_i_p], [M_i_p, M_r_p]])
        l = norm(self.vertices[1] - self.vertices[0])
        U_known = np.array([0, 1, 0, 0], float)
        rhs = -np.array(M_rhs.dot(U_known))[0]
        sol = np.linalg.lstsq(M, rhs)[0]
        length_k = len(U_known) / 2.0
        length_u = len(sol) / 2.0
        x_values = np.hstack([U_known[:length_k], sol[:length_u]])
        y_values = np.hstack([U_known[length_k:], sol[length_u:]])
        return np.array([x_values, y_values]).T

    def run_1(self):
        M = self.complex_M
        M_r = np.real(M)
        M_i = np.imag(M)
        M = np.bmat([[M_r, -M_i], [M_i, M_r]])
        _, _, v = np.linalg.svd(M)
        xy = v[:, -1]
        length_u = len(self.vertices)
        x_values = xy[:length_u]
        y_values = xy[length_u:]
        return np.array([x_values, y_values]).T[0]

    def run_2(self):
        """using (Z1 - Z0)(U2 - U0) = (Z2 - Z0)(U1 - U0) from nl"""
        M = np.ndarray([len(self.triangles) * 2, len(self.vertices) * 2], float)
        for i, tri in enumerate(self.triangles):
            verts_2d = self.triangle_to_2d(tri)
            x10, y10 = verts_2d[1] - verts_2d[0]
            x20, y20 = verts_2d[2] - verts_2d[0]

            M[2 * i, tri[0] * 2] = x20 - x10
            M[2 * i, tri[0] * 2 + 1] = -y20  # +  y10
            M[2 * i, tri[1] * 2] = -x20
            M[2 * i, tri[1] * 2 + 1] = y20
            M[2 * i, tri[2] * 2] = x10
            # M[2 * i, tri[2] * 2 + 1] = -y10

            M[2 * i + 1, tri[0] * 2] = y20  # - y10
            M[2 * i + 1, tri[0] * 2 + 1] = x20 - x10
            M[2 * i + 1, tri[1] * 2] = -y20
            M[2 * i + 1, tri[1] * 2 + 1] = -x20
            # M[2 * i + 1, tri[2] * 2] = y10
            M[2 * i + 1, tri[2] * 2 + 1] = x10

        # pinning:
        # 1: get min and max x indices
        # 2: get array of projected positions of pinned verts
        # 2.1: sort the list (lowest number first)
        # 3: create rhs and pop from matrix
        # 4: find solution and insert knowen values
        known, pin = self.get_pin_verts()
        M_r = M[:, pin]
        M = np.delete(M, pin, (1))
        rhs = np.array([M_r.dot(known)])[0]
        sol = np.linalg.lstsq(M, -rhs)[0]
        for i, pos in enumerate(pin):
            sol = np.insert(sol, pos, known[i])
        return np.array([sol[::2], sol[1::2]]).T

    @property
    def complex_M(self):
        M = np.zeros([len(self.triangles), len(self.vertices)], np.complex)
        for i, tri in enumerate(self.triangles):
            verts_2d = self.triangle_to_2d(tri)
            W = np.array(
                [
                    vector2_to_complex(verts_2d[2] - verts_2d[1]),
                    vector2_to_complex(verts_2d[0] - verts_2d[2]),
                    vector2_to_complex(verts_2d[1] - verts_2d[0]),
                ],
                np.complex,
            )
            for k, j in enumerate(tri):
                M[i, j] = W[k] / np.sqrt(self.areas[i])
        return M

    def _set_areas(self):
        for tri in self.triangles:
            a, b, c = self.vertices[tri]
            self.areas.append(norm(np.cross(b - a, c - b)))

    def triangle_to_2d(self, tri):
        """return a 2d representation of a triangle"""
        a, b, c = self.vertices[tri]
        x = a - b
        x /= norm(x)
        z = np.cross(a - c, x)
        z /= norm(z)
        y = np.cross(z, x)
        y /= norm(y)
        return self.vertices[tri].dot(np.array([x, y]).T)

    @classmethod
    def from_obj(cls, file_path):
        vertices = []
        triangles = []
        with open(file_path, "r") as _file:
            for line in _file:
                if line[0] == "v":
                    vertices.append(map(float, line.split(" ")[1:]))
                if line[0] == "f":
                    triangles.append(map(int, line.split(" ")[1:]))
        vertices = np.array(vertices)
        triangles = np.array(triangles)
        triangles -= 1
        return cls(vertices, triangles)

    def get_pin_verts(self):
        v_x = self.vertices.T[0]
        mn = v_x.argmin()
        mx = v_x.argmax()
        # sort the list
        if mn > mx:
            mx, mn = mn, mx
        known = np.array(
            [
                self.vertices[mn][0],
                self.vertices[mn][1],
                self.vertices[mx][0],
                self.vertices[mx][1],
            ]
        )
        pin = np.array([mn * 2, mn * 2 + 1, mx * 2, mx * 2 + 1])
        return known, pin


def vector2_to_complex(vector):
    return vector[0] + 1j * vector[1]


if __name__ == "__main__":
    # vertices = np.array([
    #         [0, 0., 0.5],
    #         [-1, -1, 0],
    #         [1, -1, 0],
    #         [1, 1, 0],
    #         [-1, 1, 0]
    #     ], float)

    # triangles = np.array([
    #         [0, 1, 2],
    #         [0, 2, 3],
    #         [0, 3, 4],
    #         [0, 4, 1]
    #     ], int)
    # lscm = LSCM(vertices, triangles)
    # lscm = LSCM.from_obj("/home/lo/tmp/blender/uv_1.obj")
    # lscm  =LSCM.from_obj("/home/lo/tmp/blender/uv_cylinder.obj")
    lscm = LSCM.from_obj("/home/lo/tmp/blender/uv_half_torus.obj")
    v = lscm.run_2()
    import matplotlib.pyplot as plt

    tri = lscm.triangles.T
    tri = np.array([tri[0], tri[1], tri[2], tri[0]]).T

    plt.axes().set_aspect("equal", "datalim")
    plt.plot(*v[tri].T)
    plt.show()
