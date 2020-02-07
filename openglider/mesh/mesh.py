from __future__ import division

import copy
import logging

import numpy as np
import openglider.vector as vector
import openglider.mesh.triangulate as triangulate
from openglider.mesh.poly_tri import PolyTri
USE_POLY_TRI = False
logger = logging.getLogger(__name__)


class Vertex(object):
    dmin = 10**-10

    def __init__(self, x, y, z):
        self.set_values(x, y, z)
        self.attributes = {}

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def set_values(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


    def __len__(self):
        return 3

    def copy(self):
        new = self.__class__(*self)
        new.attributes = self.attributes.copy()
        return new

    def is_equal(self, other):
        for x1, x2 in zip(self, other):
            if abs(x1 - x2) > self.dmin:
                return False
        return True

    def round(self, places):
        self.x = round(self.x, places)
        self.y = round(self.y, places)
        self.z = round(self.z, places)

    def __repr__(self):
        return super(Vertex, self).__repr__() + " {}, {}, {}\n".format(self.x, self.y, self.z)

    @classmethod
    def from_vertices_list(cls, vertices):
        return [cls(*v) for v in vertices]


class Polygon(object):
    """the polygon is a simple list, but using a Polygon-object instead of \
       a list let you monkey-patch the object"""
    def __init__(self, nodes, attributes=None):
        self.nodes = nodes
        self.attributes = attributes or {}

    def __json__(self):
        data = {
            "nodes": self.nodes
        }
        if self.attributes:
            data["attributes"] = self.attributes

        return data

    def __iter__(self):
        return self.nodes.__iter__()

    def __setitem__(self, key, value):
        return self.nodes.__setitem__(key, value)

    def __getitem__(self, item):
        return self.nodes.__getitem__(item)

    def copy(self):
        return self.__class__(self.nodes[:], self.attributes)

    def __len__(self):
        return len(self.nodes)

    def __add__(self, other):
        assert isinstance(other, Polygon)
        self.nodes += other.nodes

    @property
    def center(self):
        center = np.array([0, 0, 0], dtype=float)
        for vert in self.nodes:
            center += np.array(list(vert))
        return center / len(self.nodes)

    def get_node_average(self, attribute):
        attribute_list = [n.attributes[attribute] for n in self.nodes]
        return sum(attribute_list)/len(attribute_list)


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
        for poly_group in polygons:
            for poly in polygons[poly_group]:
                if not isinstance(poly, Polygon):
                    raise Exception("Not a polygon: {} ({})".format(poly, poly_group))
        # all nodes that might be in touch with other meshes
        self.boundary_nodes = boundary_nodes or {}
        self.name = name or "unnamed"
        self.element_groups = []

    @property
    def vertices(self):
        vertices = set()
        for poly in self.all_polygons:
            for node in poly:
                if not isinstance(node, Vertex):
                    raise Exception("Not a Vertex: {} ({})".format(node, poly))
                vertices.add(node)

        return vertices

    @property
    def all_polygons(self):
        return sum(self.polygons.values(), [])

    def copy(self):
        return copy.deepcopy(self)

    def mirror(self, axis="x"):
        for vertex in self.vertices:
            setattr(vertex, axis, -getattr(vertex, axis))

        for name, group in self.polygons.items():
            for polygon in group:
                polygon.nodes = polygon.nodes[::-1]

        return self


    def get_indexed(self):
        """
        Get [vertices, polygons, boundaries] with references by index
        """
        vertices = list(self.vertices)
        indices = {node: i for i, node in enumerate(vertices)}
        polys = {}
        for poly_name, polygons in self.polygons.items():
            poly_group = []
            for poly in polygons:
                poly_indices = [indices[node] for node in poly]
                new_poly = Polygon(poly_indices, attributes=poly.attributes)
                poly_group.append(new_poly)

            polys[poly_name] = poly_group

        boundaries = {}
        for boundary_name, boundary_nodes in self.boundary_nodes.items():
            boundaries[boundary_name] = [indices[node] for node in boundary_nodes if node in vertices]

        return vertices, polys, boundaries

    @classmethod
    def from_indexed(cls, vertices, polygons, boundaries=None, name=None, node_attributes=None):
        vertices = [Vertex(*node) for node in vertices]

        if node_attributes is not None:
            for node, attributes in zip(vertices, node_attributes):
                node.attributes.update(attributes)

        boundaries = boundaries or {}
        boundaries_new = {}
        polys = {}

        for poly_name, polygons in polygons.items():
            new_poly_group = []
            for poly in polygons:
                poly_vertices = [vertices[i] for i in poly]
                poly_attributes = getattr(poly, "attributes", {})
                new_poly = Polygon(poly_vertices, attributes=poly_attributes)
                new_poly_group.append(new_poly)

            polys[poly_name] = new_poly_group

        for boundary_name, boundary_indices in boundaries.items():
            boundaries_new[boundary_name] = [vertices[i] for i in boundary_indices]

        return cls(polys, boundaries_new, name)

    def __repr__(self):
        return "Mesh {} ({} faces, {} vertices)".format(self.name,
                                           len(self.all_polygons),
                                           len(self.vertices))

    # def copy(self):
    #     poly_copy = {key: [p.copy() for p in polygons]
    #                  for key, polygons in self.polygons.items()}
    #     return self.__class__(poly_copy, self.boundary_nodes)

    def triangularize(self):
        """
        Make triangles from quads
        """
        polys_new = {}
        for name, faces in self.polygons.items():
            faces_new = []
            for face in faces:
                if len(face) == 4:
                    faces_new.append(face[:3])
                    faces_new.append(face[2:] + face[:1])
                else:
                    faces_new.append(face)

            polys_new[name] = faces_new

        return self.__class__(polys_new)

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
            return path
        else:
            return out

    @staticmethod
    def parse_color_code(string):
        import re
        rex = re.compile(r".*#([0-9a-zA-Z]{6})")
        color = [255, 255, 255]
        match = rex.match(string)
        if match:
            color_str = match.group(1)
            color[0] = int(color_str[:2], 16)
            color[1] = int(color_str[2:4], 16)
            color[2] = int(color_str[4:], 16)

        return color

    def export_dxf(self, path=None, version="AC1021"):
        import ezdxf
        import openglider.mesh.dxf_colours as dxfcolours
        dwg = ezdxf.new(dxfversion=version)
        ms = dwg.modelspace()
        for poly_group_name, poly_group in list(self.polygons.items()):
            color = dxfcolours.get_dxf_colour_code(*self.parse_color_code(poly_group_name))
            name = poly_group_name.replace("#", "_")
            dwg.layers.new(name=name, dxfattribs={"color": color})

            polys_new = list(filter(lambda poly: len(poly) > 2, poly_group))
            if polys_new:
                mesh = Mesh({"123": polys_new})

                vertices, polys, _ = mesh.get_indexed()
                mesh_dxf = ms.add_mesh({"layer": name})

                with mesh_dxf.edit_data() as mesh_data:
                    num_posys = len(polys["123"])
                    logger.info(f"Exporting {num_polys} faces")
                    mesh_data.vertices = [list(p) for p in vertices]
                    mesh_data.faces = polys["123"]

            lines = list(filter(lambda x: len(x) == 2, poly_group))
            if lines:
                for line in lines:
                    ms.add_polyline3d([list(p) for p in line], {"layer": name})

        if path is not None:
            dwg.saveas(path)
        return dwg

    def export_ply(self, path):
        vertices, polygons, boundaries = self.get_indexed()

        material_lines = []
        panels_lines = []

        for i, polygon_group_name in enumerate(polygons):
            color = self.parse_color_code(polygon_group_name)

            color_str = " {} {} {} 1".format(*color)

            material_lines.append(" ".join([color_str]*3))

            for obj in polygons[polygon_group_name]:
                if len(obj) > 2:
                    out_str = str(len(obj))
                    for x in obj:
                        out_str += " {}".format(x)
                    out_str += " {}".format(i)
                    panels_lines.append(out_str)

        with open(path, "w") as outfile:
            outfile.write("ply\n")
            outfile.write("format ascii 1.0\n")
            outfile.write("comment exported using openglider\n")

            outfile.write("element vertex {}\n".format(len(vertices)))
            for coord in ("x", "y", "z"):
                outfile.write("property float32 {}\n".format(coord))


            # outfile.write("element material {}\n".format(len(material_lines)))
            # outfile.write("property ambient_red uchar\n")
            # outfile.write("property ambient_green uchar\n")
            # outfile.write("property ambient_blue uchar\n")
            # outfile.write("property ambient_coeff float\n")
            # outfile.write("property diffuse_red uchar\n")
            # outfile.write("property diffuse_green uchar\n")
            # outfile.write("property diffuse_blue uchar\n")
            # outfile.write("property diffuce_coeff float\n")
            # outfile.write("property specular_red uchar\n")
            # outfile.write("property specular_green uchar\n")
            # outfile.write("property specular_blue uchar\n")
            # outfile.write("property specular_coeff float\n")

            outfile.write("element face {}\n".format(len(panels_lines)))
            outfile.write("property list uchar uint vertex_indices\n")
            #outfile.write("property material_index int\n")

            outfile.write("end_header\n")

            for vertex in vertices:
                outfile.write("{:.6f} {:.6f} {:.6f}\n".format(*vertex))

            for material_line in material_lines:
                outfile.write(material_line + "\n")

            for panel_line in panels_lines:
                #print(panel_line)
                outfile.write(panel_line + "\n")

    def export_collada(self):
        # not yet working
        import collada
        mesh = collada.Collada()

        effect = collada.material.Effect("effect0", [], "phong", diffuse=(1,0,0), specular=(0,1,0))
        mat = collada.material.Material("material0", "mymaterial", effect)
        mesh.effects.append(effect)
        mesh.materials.append(mat)
        #mesh.

        # vert_src = collada.source.FloatSource("cubeverts-array", np.array(vert_floats), ('X', 'Y', 'Z'))

    def round(self, places):
        for vertice in self.vertices:
            vertice.round(places)

        return self

    def __iadd__(self, other):
        for poly_group_name, poly_group in other.polygons.items():
            self.polygons.setdefault(poly_group_name, [])
            self.polygons[poly_group_name] += poly_group
        for boundary_name, boundary in other.boundary_nodes.items():
            self.boundary_nodes.setdefault(boundary_name, [])
            self.boundary_nodes[boundary_name] += boundary
        return self

    def __add__(self, other):
        msh = self.copy()
        msh += other
        return msh

    def __getitem__(self, item):
        polys = self.polygons[item]
        new_mesh = Mesh(polygons={item: polys})
        vertices = new_mesh.vertices
        boundaries = {}

        for boundary_name, boundary_nodes in self.boundary_nodes.items():
            new_vertices = []
            for node in boundary_nodes:
                if node in vertices:
                    new_vertices.append(node)

            if new_vertices:
                boundaries[boundary_name] = new_vertices

        new_mesh.boundary_nodes = boundaries

        return new_mesh


    # def __iadd__(self, other):
    #     self = self + other

    def delete_duplicates(self, boundaries=None):
        """
        :param boundaries: list of boundary names to be joined (None->all)
        :return: Mesh (self)
        """

        boundaries = boundaries or self.boundary_nodes.keys()
        replace_dict = {}
        all_boundary_nodes = sum([self.boundary_nodes[name] for name in boundaries], [])

        for i, node1 in enumerate(all_boundary_nodes[:-1]):
            if node1 not in replace_dict:
                for j, node2 in enumerate(all_boundary_nodes[i:]):
                    if node1 is not node2 and node1.is_equal(node2):
                        replace_dict[node2] = node1
                        node1.attributes.update(node2.attributes)

        for boundary_name, boundary_nodes in self.boundary_nodes.items():
            to_remove = []
            for i, node in enumerate(boundary_nodes):
                if node in replace_dict:
                    to_remove.append(i)
            for i in to_remove[::-1]:
                boundary_nodes.pop(i)

            if to_remove:
                count = len(to_remove)
                logger.info(f"deleted {count} duplicated Vertices for boundary group <{boundary_name}> ")

        for polygon in self.all_polygons:
            for i, node in enumerate(polygon):
                if node in replace_dict:
                    polygon[i] = replace_dict[node]

        # delete duplicated nodes in every element
        polygons = []
        for group_name, poly_group in self.polygons.items():
            for i, polygon in enumerate(poly_group):
                poly_set = set(polygon)
                new_polygon = Polygon([node for node in polygon if node in poly_set])
                new_polygon.attributes = polygon.attributes
                self.polygons[group_name][i] = new_polygon

        vertices = self.vertices
        for boundary_name in boundaries:
            for i, node in enumerate(self.boundary_nodes[boundary_name]):
                if node not in vertices:
                    logger.warning(f"uiuiui, {node} in replace dict is not in vertices")
        return self

    def polygon_size(self):
        size_min = float("inf")
        size_max = float("-inf")
        count = 0
        sum = 0

        for poly in self.all_polygons:
            if len(poly) in (3, 4):
                sides = []
                for i in range(len(poly)):
                    i_plus = i+1
                    if i_plus == len(poly):
                        i_plus = 0
                    side = np.array(list(poly[i])) - np.array(list(poly[i_plus]))
                    sides.append(side)

                if len(poly) == 3:
                    size_poly = 0.5 * vector.norm(np.cross(sides[0], sides[1]))
                elif len(poly) == 4:
                    size_poly = 0.5 * (vector.norm(np.cross(sides[0], sides[1])) + vector.norm(np.cross(sides[2], sides[3])))
                else:
                    size_poly = 0

                sum += size_poly
                count += 1

                size_min = min(size_min, size_poly)
                size_max = max(size_max, size_poly)

        return size_min, size_max, sum/count


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

