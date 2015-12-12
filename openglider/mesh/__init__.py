from __future__ import division
import numpy as np
import meshpy.triangle as mptriangle
from openglider.mesh.meshpy_triangle import custom_triangulation


class mesh(object):
    """
    Mesh Surface: vertices and polygons
    """
    def __init__(self, vertices=None, polygons=None):
        self.vertices = vertices
        self.polygons = polygons or []

    @classmethod
    def from_rib(cls, rib):
        profile = rib.profile_2d
        triangle_in = {}
        vertices = list(profile.data)
        segments = [[i, i+1] for i, _ in enumerate(vertices[:-1])]
        segments[-1][-1] = 0
        triangle_in["vertices"] = vertices[:-1]
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

        # _triangle_output = triangle.triangulate(triangle_in, "pziq")
        mesh_info = mptriangle.MeshInfo()
        mesh_info.set_points(triangle_in["vertices"])
        mesh_info.set_facets(triangle_in["segments"])
        if "holes" in triangle_in:
            mesh_info.set_holes(triangle_in["holes"])
        mesh = custom_triangulation(mesh_info, "Qzip")
        try:
            # vertices = rib.align_all(_triangle_output["vertices"])
            # triangles = _triangle_output["triangles"]
            vertices = rib.align_all(np.array(mesh.points))
            triangles = list(mesh.elements)
        except KeyError:
            print("there was an keyerror")
            return cls()
        return cls(vertices, triangles)

    @classmethod
    def from_diagonal(cls, diagonal, cell, insert_points=0):
        left, right = diagonal.get_3d(cell)
        if insert_points:
            point_array = []
            number_array = []
            # create array of points
            # the outermost points build the segments
            n_l = len(left)
            n_r = len(right)
            count = 0
            for y_pos in np.linspace(0., 1., insert_points + 2):
                # from left to right
                point_line = []
                number_line = []
                num_points = int(n_l * (1. - y_pos) + n_r * y_pos)
                for x_pos in np.linspace(0., 1., num_points):
                    point_line.append(left[x_pos * (n_l - 1)] * (1. - y_pos) + 
                                      right[x_pos * (n_r - 1)] * y_pos)
                    number_line.append(count)
                    count += 1
                point_array.append(point_line)
                number_array.append(number_line)
            edge = number_array[0]
            edge += [line[-1] for line in number_array[1:]]
            edge += number_array[-1][-2::-1] # last line reversed without the last element
            edge += [line[0] for line in number_array[1:-1]][::-1]
            segment = [[edge[i], edge[i +1]] for i in range(len(edge) - 1)]
            segment.append([edge[-1], edge[0]])
            point_array = np.array([point for line in point_array for point in line])
            points2d = map_to_2d(point_array)

            mesh_info = meshpy_triangle.MeshInfo()
            mesh_info.set_points(points2d)
            mesh = custom_triangulation(mesh_info, "Qz")
            return cls(point_array, list(mesh.elements))

        else:
            vertices = np.array(list(left) + list(right)[::-1])
            polygon = [range(len(vertices))]
            return cls(vertices, polygon)


    def __add__(self, other):
        if None in (other.vertices, other.polygons):
            return self
        if None in (self.vertices, self.polygons):
            return other
        else:
            new_mesh = mesh()
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



def map_to_2d(points):
    """ map points to 2d least square plane
     min([x, y, z, 1] * [A, B, C, D].T)"""
    mat = np.array(points).T
    mat = np.array([mat[0], mat[1], mat[2], np.ones(len(mat[0]))])
    u, d, v = np.linalg.svd(mat.T)
    n = v[-1][0:3]
    l_n = np.linalg.norm(n)
    n /= l_n
    x = np.cross(n, n[::-1])
    y = np.cross(n, x)
    to_2d_mat = np.array([x, y]).T
    return np.array(points).dot(to_2d_mat)
            

if __name__ == "__main__":
    a = mesh()
    b = mesh()
    a.vertices = np.array([[0,0],[1,2],[2,3]])
    b.vertices = np.array([[0,0],[1,2],[2,3]])
    a.outer_faces = np.array([[0, 1, 2]])
    b.outer_faces = np.array([[0, 1, 2]])
    a.triangles = np.array([[0, 1, 2]])
    b.triangles = np.array([[0, 1, 2]])
    c = a + b
    print(c.triangles)



