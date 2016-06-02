from __future__ import division

import numpy as np
import meshpy.triangle as mptriangle

from openglider.mesh.meshpy_triangle import custom_triangulation


class Vertex(object):
    dmin = 10**-3

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def copy(self):
        return self.__class__(*self)

    def is_equal(self, other):
        for x1, x2 in zip(self, other):
            if abs(x1 - x2) > self.dmin:
                return False
        return True

    def __repr__(self):
        return super(Vertex, self).__repr__() + " {}, {}, {}\n".format(self.x, self.y, self.z)

    @staticmethod
    def from_vertices_list(vertices):
        return [Vertex(*v) for v in vertices]


class Polygon(list):
    """the polygon is a simple list, but using a Polygon-object instead of \
       a list let you monkey-patch the object"""
    pass

class Mesh(object):
    """
    Mesh Surface: vertices and polygons

    A mesh has vertices, polygons and boundary information.
    polygons can be:
        line (2 vertices)
        triangle (3 vertices)
        quadrangle (4 vertices)
    """
    def __init__(self, polygons=None, boundary_nodes=None, name=None):
        """

        """
        if polygons is None:
            polygons = {}
        self.polygons = polygons
        assert all(isinstance(vertex, Vertex) for vertex in self.vertices)
        # all nodes that might be in touch with other meshes
        self.boundary_nodes = boundary_nodes or {}
        self.name = name or "unnamed"
        self.element_groups = []

    @property
    def vertices(self):
        vertices = set()
        for poly in self.all_polygons:
            for node in poly:
                vertices.add(node)

        return vertices

    @property
    def all_polygons(self):
        return sum(self.polygons.values(), [])

    def get_indexed(self):
        """
        Get [vertices, polygons, boundaries] with references by index
        """
        vertices = list(self.vertices)
        indices = {node: i for i, node in enumerate(vertices)}
        polys = {}
        for poly_name, polygons in self.polygons.items():
            polys[poly_name] = [[indices[node] for node in poly] for poly in polygons]
        boundaries = {}
        for boundary_name, boundary_nodes in self.boundary_nodes.items():
            boundaries[boundary_name] = [indices[node] for node in boundary_nodes]

        return vertices, polys, boundaries

    @classmethod
    def from_indexed(cls, vertices, polygons, boundaries=None, name=None):
        vertices = [Vertex(*node) for node in vertices]
        boundaries = boundaries or {}
        boundaries_new = {}
        polys = {}
        for poly_name, polygons in polygons.items():
            polys[poly_name] = [[vertices[i] for i in poly] for poly in polygons]
        for boundary_name, boundary_indices in boundaries.items():
            boundaries_new[boundary_name] = [vertices[i] for i in boundary_indices]

        return cls(polys, boundaries_new, name)

    def __repr__(self):
        return "Mesh {} ({} faces, {} vertices)".format(self.name,
                                           len(self.all_polygons),
                                           len(self.vertices))

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
        return cls.from_indexed(vertices, polygons={"ribs": triangles})# , boundaries=connection)

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

            mesh_info = mptriangle.MeshInfo()
            mesh_info.set_points(points2d)
            mesh = custom_triangulation(mesh_info, "Qz")
            return cls.from_indexed(point_array, {"diagonals": list(mesh.elements)})

        else:
            vertices = np.array(list(left) + list(right)[::-1])
            polygon = [range(len(vertices))]
            return cls.from_indexed(vertices, {"diagonals": polygon})

    def copy(self):
        poly_copy = {key: [[v for v in p] for p in polygons]
                     for key, polygons in self.polygons.items()}
        return self.__class__(poly_copy, self.boundary_nodes)

    def triangularize(self):
        """
        Make triangles from quads
        """
        faces_new = []
        for face in self.polygons:
            if len(face) == 4:
                faces_new.append(face[:3])
                faces_new.append(face[2:] + face[:1])
            else:
                faces_new.append(face)

        return self.__class__(self.vertices, faces_new)

    def __json__(self):
        vertices, polygons, boundaries = self.get_indexed()
        vertices_new = [list(v) for v in vertices]
        return {
            "vertices": vertices_new,
            "polygons": polygons,
            "boundaries": boundaries,
            "name": self.name
        }

    __from_json__ = from_indexed

    #@classmethod
    #def __from_json__(cls, vertices, polygons, boundaries, name):
    #    return cls.from_indexed(vertices, polygons, boundaries, name)

    def export_obj(self, path=None, offset=0):
        vertices, polygons, boundaries = self.get_indexed()
        out = ""

        for vertex in vertices:
            out += "v {:.6f} {:.6f} {:.6f}\n".format(*vertex)

        for polygon_group_name, polygons in polygons.items():
            out += "o {}\n".format(polygon_group_name)
            for obj in polygons:
                if len(obj) == 2:
                    # line
                    code = "l"
                else:
                    # face
                    code = "f"

                out += " ".join([code] + [str(x+offset+1) for x in obj])
                out += "\n"

        if path:
            with open(path, "w") as outfile:
                outfile.write(out)

        return out

    def __add__(self, other):
        msh = self.copy()
        for poly_group_name, poly_group in other.polygons.items():
            msh.polygons.setdefault(poly_group_name, [])
            msh.polygons[poly_group_name] += poly_group
        for boundary_name, boundary in other.boundary_nodes.items():
            msh.boundary_nodes.setdefault(boundary_name, [])
            msh.boundary_nodes[boundary_name] += boundary

        return msh


    # def __iadd__(self, other):
    #     self = self + other

    def delete_duplicates(self, boundaries=None):
        """
        :param boundaries: list of boundary names to be joined (None->all)
        :return: Mesh (self)
        """

        boundaries = boundaries or self.boundary_nodes.keys()
        replace_dict = {}

        for boundary_name in boundaries:
            replace_dict_this = {}
            # remove duplicates
            boundary_nodes = self.boundary_nodes[boundary_name]
            # go through all nodes
            for i, node1 in enumerate(boundary_nodes[:-1]):
                # skip if already detected
                if node1 not in replace_dict_this:
                    for j, node2 in enumerate(boundary_nodes[i+1:]):
                        # check distance and replace if samesame
                        if node1 is not node2 and node1.is_equal(node2):
                            replace_dict_this[node2] = node1

            for replaced_node in replace_dict_this.keys():
                boundary_nodes.remove(replaced_node)
            print("deleted {} duplicated Vertices for boundary group <{}> ".format(
                    len(replace_dict_this), boundary_name))
            replace_dict.update(replace_dict_this)

            self.boundary_nodes[boundary_name] = boundary_nodes

        for polygon in self.all_polygons:
            for i, node in enumerate(polygon):
                if node in replace_dict:
                    polygon[i] = replace_dict[node]

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
    p1 = Vertex(*[0, 0, 0])
    p2 = Vertex(*[1, 0, 0])
    p3 = Vertex(*[0, 1, 0])
    p4 = Vertex(*[1, 1, 0])
    p5 = Vertex(*[0, 0, 0])
    print(p1)

    a = Polygon([p1,p2,p3,p4])
    b = Polygon([p1,p2,p4,p5])

    m1 = Mesh({"a": [a]}, boundary_nodes={"j": a})
    m2 = Mesh({"b": [b]}, boundary_nodes={"j": b})

    m1 += m2
    m1.delete_duplicates()
    print(m1.polygons)

