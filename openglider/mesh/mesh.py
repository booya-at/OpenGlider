from __future__ import division
import copy

import numpy as np
import meshpy.triangle as mptriangle

from openglider.mesh.meshpy_triangle import custom_triangulation


class Mesh(object):
    """
    Mesh Surface: vertices and polygons
    """
    def __init__(self, vertices=None, polygons=None, connection=None, name="unnamed"):
        """ A mesh has vertices, polygons and connection information.
            polygons can be:
                line (2 indices)
                triangle (3 vertices)
                quadrangle (4 vertices)
        """
        self.vertices = vertices            # np array of all vertices
        if self.vertices is None:
            self.vertices = np.array([], float).reshape(0, 3)
        self.polygons = polygons or []      # list of all element indices
        self.connection = connection or {}  # store all the connection info
        self.name = name

    def __repr__(self):
        return "Mesh {} ({} vertices, {} faces)".format(self.name,
                                                        len(self.vertices),
                                                        len(self.polygons))

    @classmethod
    def from_rib(cls, rib, hole_num=10, mesh_option="Qzip"):
        """ Y... no additional points on boarder
            i... algorythm (other algo crash)
            p... triangulation
            q... quality
            a... area constraint
        """
        profile = rib.profile_2d
        triangle_in = {}
        vertices = list(profile.data)[:-1]
        connection = {rib: np.array(range(len(vertices)))}
        segments = [[i, i+1] for i, _ in enumerate(vertices)]
        segments[-1][-1] = 0
        triangle_in["vertices"] = vertices
        triangle_in["segments"] = segments

        # adding the vertices and segments of the holes
        # to get TRIANGLE know where to remove triangles
        # a list of points which lay inside the holes
        # must be passed
        if len(rib.holes) > 0 and hole_num > 3:
            triangle_in["holes"] = []
            for nr, hole in enumerate(rib.holes):
                start_index = len(triangle_in["vertices"])
                hole_vertices = hole.get_flattened(rib, num=hole_num, scale=False)
                segments = [[i + start_index, i + start_index + 1] for i, _ in enumerate(hole_vertices)]
                segments[-1][-1] = start_index
                triangle_in["vertices"] += hole_vertices
                triangle_in["segments"] += segments
                triangle_in["holes"].append(hole.get_center(rib, scale=False).tolist())

        # _triangle_output = triangle.triangulate(triangle_in, "pziq")
        mesh_info = mptriangle.MeshInfo()
        mesh_info.set_points(triangle_in["vertices"])
        mesh_info.set_facets(triangle_in["segments"])
        if "holes" in triangle_in:
            mesh_info.set_holes(triangle_in["holes"])
        mesh = custom_triangulation(mesh_info, mesh_option)  # see triangle options
        try:
            triangles = list(mesh.elements)
            vertices = rib.align_all(mesh.points)
        except KeyError:
            print("there was a keyerror")
            return cls()
        return cls(vertices, triangles, connection)

    @classmethod
    def from_diagonal(cls, diagonal, cell, insert_points=4):
        """
        get a mesh from a diagonal (2 poly lines)
        """
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

    def copy(self):
        poly_copy = [p[:] for p in self.polygons]
        return self.__class__(self.vertices, poly_copy)

    def triangularize(self):
        """
        Make triangles from quads
        """
        faces_new = []
        for face in self.polygons:
            if len(face) == 3:
                faces_new.append(face)
            elif len(face) == 4:
                faces_new.append(face[:3])
                faces_new.append(face[2:] + face[:1])

        return self.__class__(self.vertices, faces_new)

    def __json__(self):
        return {
            "vertices": self.vertices.tolist(),
            "polygons": self.polygons
        }

    def export_obj(self, path=None, offset=0):
        out = "o {}\n".format(self.name)
        for vertice in self.vertices:
            out += "v {:.6f} {:.6f} {:.6f}\n".format(*vertice)

        for obj in self.polygons:
            if len(obj) == 2:
                code = "l"
            else:
                code = "f"

            out += " ".join([code] + [str(x+offset+1) for x in obj])
            out += "\n"

        if path:
            with open(path, "w") as outfile:
                outfile.write(out)

        return out

    def __add__(self, other):
        """adding two mesh objects"""
        # copy the mesh, otherwise the input mesh get changed
        new_mesh = Mesh(copy.copy(self.vertices),
                        copy.copy(self.polygons),
                        copy.copy(self.connection))
        # translate to a python list for easier manipulation
        vertices_list = self.vertices.tolist()
        count = len(vertices_list)
        # connection information stored in both meshes
        intersections = (set(self.connection.keys()) &
                         set(other.connection.keys()))
        # create a map from connection info
        connect_rules = dict()
        for intersect in intersections:
            for j, index in enumerate(other.connection[intersect]):
                connect_rules[index] = self.connection[intersect][j]
        # mapping other.vertices
        replace_rules = dict()
        for i, vertex in enumerate(other.vertices):
            value = connect_rules.get(i)
            if value is not None:
                replace_rules[i] = value
                count -= 1
            else:
                replace_rules[i] = i+count
                vertices_list.append(vertex)
        # apply the replacement rules
        new_mesh.polygons += [
            [replace_rules[index] for index in pol] for pol in other.polygons]
        new_mesh.vertices = np.array(vertices_list)

        for key in other.connection.keys():
            if key not in intersections:
                new_mesh.connection[key] = [
                    replace_rules[value] for value in other.connection[key]]
        return new_mesh

    def delete_duplicates(self, min_dist=10**(-10)):
        """
        delete points that are close to each other
        """
        replace_dict = {}
        for i, point_i in enumerate(self.vertices[:-1]):
            if not i in replace_dict:
                for j, point_j in enumerate(self.vertices[i+1:]):
                    _j = j + i + 1
                    if not _j in replace_dict:
                        if np.linalg.norm(point_j - point_i) < min_dist:
                            replace_dict[_j] = i
        for j, point_j in enumerate(self.vertices):
            if j not in replace_dict:
                replace_dict[j] = j
        self.apply_rules(replace_dict)
        self.delete_vertices_not_used()

    def apply_rules(self, rules):
        """apply a dict of replacement rules to the polygons"""
        self.polygons = [[rules[index] for index in pol] for pol in self.polygons]
        new_connection_info = {}
        for key in self.connection:
            new_connection_info[key] = [rules[i] for i in self.connection[key]]
        self.connection = new_connection_info

    def delete_vertices_not_used(self):
        """delete all vertices not used in the polygons"""
        sorted_indices = list(sorted(set(index for pol in self.polygons for index in pol)))#
        self.apply_rules({value: j for j, value in enumerate(sorted_indices)})
        self.vertices = np.array([point for j, point in enumerate(self.vertices) if j in sorted_indices])


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
    a = Mesh(np.array([[0,0,0], [0,1,0], [1,0,0]]), [[0,1,2]])
    b = Mesh(np.array([[0,0,0], [0,1,0], [-1,0,0]]), [[0,2,1]])
    c = a + b
    c.delete_duplicates(0.1)