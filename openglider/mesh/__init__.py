from __future__ import division
import triangle
import numpy as np

class mesh_2d(object):
    def __init__(self, vertices=None, polygons=None):
        self.vertices = vertices
        self.polygons = polygons

    @classmethod
    def from_rib(cls, rib):
        profile = rib.profile_2d
        triangle_in = {}
        vertices = list(profile.data)
        segments = [[i, i+1] for i, _ in enumerate(vertices)]
        segments[-1][-1] = 0
        triangle_in["vertices"] = vertices
        triangle_in["segments"] = segments

        # adding the vertices and segments of the holes
        # to get TRIANGLE know where to remove triangles
        # a list of points which lay inside the holes
        # must be passed
        if len(rib.holes) > 0:
            triangle_in["holes"] = []
            for nr, hole in enumerate(rib.holes):
                start_index = len(triangle_in["vertices"])
                vertices = hole.get_flattened(rib, num=10, scale=False)
                segments = [[i + start_index, i + start_index + 1] for i, _ in enumerate(vertices)]
                segments[-1][-1] = start_index
                triangle_in["vertices"] += vertices
                triangle_in["segments"] += segments
                triangle_in["holes"].append(hole.get_center(rib, scale=False).tolist())

        _triangle_output = triangle.triangulate(triangle_in)
        try:
            vertices = rib.align_all(_triangle_output["vertices"])
            triangles = _triangle_output["triangles"]
        except KeyError:
            print("there was an keyerror")
            return cls()
        obj = cls(vertices, triangles.tolist())
        return obj

    @classmethod
    def from_diagonal(cls, diagonal, cell):
        left, right = diagonal.get_3d(cell)
        vertices = np.array(list(left) + list(right)[::-1])
        polygon = [range(len(vertices))]
        return cls(vertices, polygon)


    def __add__(self, other):
        if None in (other.vertices, other.polygons):
            return self
        if None in (self.vertices, self.polygons):
            return other
        else:
            new_mesh = mesh_2d()
            new_mesh.vertices = np.concatenate([self.vertices, other.vertices])
            start_value = float(len(self.vertices))
            new_other_polygons = [[val + start_value for val in tri] for tri in other.polygons]
            new_mesh.polygons = self.polygons + new_other_polygons
            return new_mesh

    def __iadd__(self, other):
        if None in (other.vertices, other.polygons):
            return self
        if None in (self.vertices, self.polygons):
            return other
        else:
            start_value = float(len(self.vertices))
            new_other_polygons = [[val + start_value for val in tri] for tri in other.polygons]
            self.polygons = self.polygons + new_other_polygons
            self.vertices = np.concatenate([self.vertices, other.vertices])
            return self

def apply_z(vertices):
    v = vertices.T
    return np.array([v[0], np.zeros(len(v[0]), v[1])]).T


if __name__ == "__main__":
    a = mesh_2d()
    b = mesh_2d()
    a.vertices = np.array([[0,0],[1,2],[2,3]])
    b.vertices = np.array([[0,0],[1,2],[2,3]])
    a.outer_faces = np.array([[0, 1, 2]])
    b.outer_faces = np.array([[0, 1, 2]])
    a.triangles = np.array([[0, 1, 2]])
    b.triangles = np.array([[0, 1, 2]])
    c = a + b
    print(c.triangles)



