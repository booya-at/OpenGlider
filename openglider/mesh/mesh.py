from __future__ import annotations
from pathlib import Path

from typing import Any, List, Dict, Literal, Tuple, TypeAlias, Union
from collections.abc import Iterator, Sequence, Sized
import copy
import logging

import euklid
import ezdxf
import ezdxf.document

import openglider.mesh.dxf_colours as dxfcolours
from openglider.mesh.triangulate import Triangle

USE_POLY_TRI = False
logger = logging.getLogger(__name__)


class Vertex:
    _position: euklid.vector.Vector3D

    dmin = 10**-10

    def __init__(self, x: float, y: float, z: float, attributes: dict[str, Any]=None):
        self._position = euklid.vector.Vector3D([x,y,z])
        self.attributes = attributes or {}
        self.index = -1

    def __iter__(self) -> Iterator[float]:
        return self.position.__iter__()
    
    @property
    def position(self) -> euklid.vector.Vector3D:
        return self._position
    
    @property
    def x(self) -> float:
        return self.position[0]
    @property
    def y(self) -> float:
        return self.position[1]
    @property
    def z(self) -> float:
        return self.position[2]

    def __json__(self) -> list[Any]:
        data: list[Any] = list(self)
        if self.attributes:
            data.append(self.attributes)

        return data

    def set_values(self, x: float, y: float, z: float) -> None:
        self._position = euklid.vector.Vector3D([x,y,z])

    def __len__(self) -> Literal[3]:
        return 3

    def copy(self) -> Vertex:
        new = self.__class__(*self)
        new.attributes = self.attributes.copy()
        return new

    def is_equal(self, other: Vertex) -> bool:
        for x1, x2 in zip(self, other):
            if abs(x1 - x2) > self.dmin:
                return False
        return True

    def is_in_range(self, minimum: euklid.vector.Vector3D, maximum: euklid.vector.Vector3D) -> bool:
        return (self.position[0] >= minimum[0] and self.position[1] >= minimum[1] and self.position[2] >= minimum[2] and
                self.position[0] <= maximum[0] and self.position[1] <= maximum[1] and self.position[2] <= maximum[2])

    def round(self, places: int) -> None:
        self.position[0] = round(self.position[0], places)
        self.position[1] = round(self.position[1], places)
        self.position[2] = round(self.position[2], places)

    def __repr__(self) -> str:
        return super().__repr__() + f" {self.position[0]}, {self.position[1]}, {self.position[2]}\n"

    @classmethod
    def from_vertices_list(cls, vertices: list[Any]) -> list[Vertex]:
        return [cls(*v) for v in vertices]


class Polygon:
    """the polygon is a simple list, but using a Polygon-object instead of \
       a list let you monkey-patch the object"""
    def __init__(self, nodes: list[Vertex], attributes: dict[str, Any]=None):
        self.nodes = nodes
        self.attributes = attributes or {}

    def __json__(self) -> dict[str, Any]:
        data = {
            "nodes": self.nodes,
            "attributes": self.attributes
        }

        return data

    def __iter__(self) -> Iterator[Vertex]:
        return self.nodes.__iter__()

    def __setitem__(self, key: int, value: Vertex) -> None:
        return self.nodes.__setitem__(key, value)

    def __getitem__(self, item: int) -> Vertex:
        return self.nodes.__getitem__(item)

    def copy(self) -> Polygon:
        return self.__class__(self.nodes[:], self.attributes)

    def __len__(self) -> int:
        return len(self.nodes)

    def __add__(self, other: Polygon) -> None:
        assert isinstance(other, Polygon)
        self.nodes += other.nodes

    @property
    def center(self) -> euklid.vector.Vector3D:
        center = euklid.vector.Vector3D([0,0,0])
        for vert in self.nodes:
            center += vert.position
        return center / len(self.nodes)
    
    def _get_normal(self) -> euklid.vector.Vector3D:
        if len(self) == 2:
            n = self.nodes[1].position - self.nodes[0].position

        elif len(self) == 3:
            l1 = self.nodes[1].position-self.nodes[0].position
            l2 = self.nodes[0].position-self.nodes[2].position
            n = l1.cross(l2)

        elif len(self) == 4:
            l1 = self.nodes[2].position-self.nodes[0].position
            l2 = self.nodes[3].position-self.nodes[1].position
            n = l1.cross(l2)
        
        return n


    @property
    def normal(self) -> euklid.vector.Vector3D:
        return self._get_normal().normalized()
    
    @property
    def area(self) -> float:
        return self._get_normal().length() * 0.5



    def get_node_average(self, attribute: str) -> Any:
        attribute_list = [n.attributes[attribute] for n in self.nodes]
        return sum(attribute_list)/len(attribute_list)


PolygonType: TypeAlias = Union[tuple[int, int], tuple[int, int, int], tuple[int, int, int, int]] | Triangle

class Mesh:
    """
    Mesh Surface: vertices and polygons

    A mesh has vertices, polygons and boundary information.
    polygons can be:
        line (2 vertices)
        triangle (3 vertices)
        quadrangle (4 vertices)
    """
    boundary_nodes_type = dict[str, list[int]]

    def __init__(self, polygons: dict[str, list[Polygon]]=None, boundary_nodes: dict[str, list[Vertex]]=None, name: str="unnamed"):
        self.polygons = polygons or {}

        # all nodes that might be in touch with other meshes
        self.boundary_nodes = boundary_nodes or {}

        self.name = name

    @property
    def vertices(self) -> list[Vertex]:
        vertices = set()
        for poly in self.get_all_polygons():
            for node in poly:
                if not isinstance(node, Vertex):
                    raise Exception(f"Not a Vertex: {node} ({poly})")
                vertices.add(node)

        return list(vertices)

    @property
    def bounding_box(self) -> tuple[euklid.vector.Vector3D, euklid.vector.Vector3D]:
        vertices_x = [p.x for p in self.vertices]
        vertices_y = [p.y for p in self.vertices]
        vertices_z = [p.z for p in self.vertices]

        return euklid.vector.Vector3D([min(vertices_x), min(vertices_y), min(vertices_z)]), euklid.vector.Vector3D([max(vertices_x), max(vertices_y), max(vertices_z)])

    def get_all_polygons(self) -> list[Polygon]:
        return sum(self.polygons.values(), [])


    def copy(self) -> Mesh:
        return copy.deepcopy(self)

    def mirror(self, axis: Literal["x"] | Literal["y"] | Literal["z"]="x") -> Mesh:
        multiplication = {
            "x": euklid.vector.Vector3D([-1, 1, 1]),
            "y": euklid.vector.Vector3D([1, -1, 1]),
            "z": euklid.vector.Vector3D([1, 1, -1])
        }[axis]
        for vertex in self.vertices:
            vertex._position = vertex._position * multiplication

        for name, group in self.polygons.items():
            for polygon in group:
                if len(polygon) > 2:
                    polygon.nodes = polygon.nodes[::-1]

        return self


    def get_indexed(self) -> tuple[list[Vertex], dict[str, list[tuple[PolygonType, dict[str, Any]]]], dict[str, list[int]]]:
        """
        Get [vertices, polygons, boundaries] with references by index
        """
        vertices: list[Vertex] = list(self.vertices)
        for i, v in enumerate(vertices):
            v.index = i
            
        polygons: dict[str, list[tuple[PolygonType, dict[str, Any]]]] = {}

        for poly_name, polygon_group in self.polygons.items():
            poly_group: list[tuple[PolygonType, dict[str, Any]]] = []

            for poly in polygon_group:
                poly_group.append((
                    tuple(node.index for node in poly),  # type: ignore
                    poly.attributes
                ))

            polygons[poly_name] = poly_group


        boundaries = {}
        for boundary_name, boundary_nodes in self.boundary_nodes.items():
            boundaries[boundary_name] = [node.index for node in boundary_nodes if node in vertices]

        return vertices, polygons, boundaries

    @classmethod
    def from_indexed(
        cls,
        vertices: list[euklid.vector.Vector3D],
        polygons: dict[str, Sequence[tuple[PolygonType, dict[str, Any]]]],
        boundaries: dict[str, list[int]]=None,
        name: str="unnamed",
        node_attributes: list[dict[str, Any]]=None,
        ) -> Mesh:

        _vertices = [Vertex(*node) for node in vertices]

        if node_attributes is not None:
            for node, attributes in zip(_vertices, node_attributes):
                node.attributes.update(attributes)

        boundaries = boundaries or {}
        boundaries_new = {}
        polys = {}

        for polygon_group_name, polygon_group in polygons.items():
            new_polygon_group = []
            for polygon in polygon_group:
                poly_vertices = [_vertices[p] for p in polygon[0]]
                poly_attributes = polygon[1]

                new_poly = Polygon(poly_vertices, attributes=poly_attributes)
                new_polygon_group.append(new_poly)

            polys[polygon_group_name] = new_polygon_group

        for boundary_name, boundary_indices in boundaries.items():
            boundaries_new[boundary_name] = [_vertices[i] for i in boundary_indices]

        return cls(polys, boundaries_new, name)

    def __repr__(self) -> str:
        return "Mesh {} ({} faces, {} vertices)".format(self.name,
                                           len(self.get_all_polygons()),
                                           len(self.vertices))

    # def copy(self):
    #     poly_copy = {key: [p.copy() for p in polygons]
    #                  for key, polygons in self.polygons.items()}
    #     return self.__class__(poly_copy, self.boundary_nodes)

    def triangularize(self) -> Mesh:
        """
        Make triangles from quads
        """
        polys_new = {}
        for name, faces in self.polygons.items():
            faces_new: list[Polygon] = []
            for face in faces:
                if len(face) == 4:
                    faces_new.append(Polygon(face.nodes[:3], attributes=face.attributes))
                    faces_new.append(Polygon(face.nodes[2:] + face.nodes[:1], attributes=face.attributes))
                else:
                    faces_new.append(face)

            polys_new[name] = faces_new

        return self.__class__(polys_new)

    def __json__(self) -> dict[str, Any]:
        vertices, polygons, boundaries = self.get_indexed()
        vertices_new = [v.__json__() for v in vertices]

        return {
            "vertices": vertices_new,
            "polygons": polygons,
            "boundaries": boundaries,
            "name": self.name
        }

    __from_json__ = from_indexed

    def export_obj(self, path: str | Path | None=None, offset: float=0) -> str:
        vertices, polygons, boundaries = self.get_indexed()
        out = ""

        for vertex in vertices:
            out += "v {:.6f} {:.6f} {:.6f}\n".format(*vertex)

        for polygon_group_name, group_polygons in polygons.items():
            out += f"o {polygon_group_name}\n"
            for obj, _attributes in group_polygons:
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
        else:
            return out

    @staticmethod
    def parse_color_code(string: str) -> tuple[int, int, int]:
        import re
        rex = re.compile(r".*#([0-9a-zA-Z]{6})")
        match = rex.match(string)
        if match:
            color_str = match.group(1)
            return (
                int(color_str[:2], 16),
                int(color_str[2:4], 16),
                int(color_str[4:], 16)
            )

        return (255, 255, 255)

    def export_dxf(self, path: str | Path | None=None, version: str="AC1021") -> ezdxf.document.Drawing:
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
                    num_polys = len(polys["123"])
                    logger.info(f"Exporting {num_polys} faces")
                    mesh_data.vertices = [list(p) for p in vertices]  # type: ignore
                    mesh_data.faces = [list(p[0]) for p in polys["123"]]  # type: ignore

            lines = list(filter(lambda x: len(x) == 2, poly_group))
            if lines:
                for line in lines:
                    ms.add_polyline3d([list(p) for p in line], dxfattribs={"layer": name})

        if path is not None:
            dwg.saveas(path)
        return dwg

    def export_ply(self, path: str | Path) -> None:
        vertices, polygons, _boundaries = self.get_indexed()

        material_lines = []
        panels_lines = []

        for i, polygon_group_name in enumerate(polygons):
            color = self.parse_color_code(polygon_group_name)

            color_str = " {} {} {} 1".format(*color)

            material_lines.append(" ".join([color_str]*3))

            for obj, _attributes in polygons[polygon_group_name]:
                if len(obj) > 2:
                    out_str = str(len(obj))
                    for x in obj:
                        out_str += f" {x}"
                    out_str += f" {i}"
                    panels_lines.append(out_str)

        with open(path, "w") as outfile:
            outfile.write("ply\n")
            outfile.write("format ascii 1.0\n")
            outfile.write("comment exported using openglider\n")

            outfile.write(f"element vertex {len(vertices)}\n")
            for coord in ("x", "y", "z"):
                outfile.write(f"property float32 {coord}\n")


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

            outfile.write(f"element face {len(panels_lines)}\n")
            outfile.write("property list uchar uint vertex_indices\n")
            #outfile.write("property material_index int\n")

            outfile.write("end_header\n")

            for vertex in vertices:
                outfile.write("{:.6f} {:.6f} {:.6f}\n".format(*vertex))

            for material_line in material_lines:
                outfile.write(material_line + "\n")

            for panel_line in panels_lines:
                outfile.write(panel_line + "\n")

    def round(self, places: int) -> Mesh:
        for vertice in self.vertices:
            vertice.round(places)

        return self

    def __iadd__(self, other: Mesh) -> Mesh:
        for poly_group_name, poly_group in other.polygons.items():
            self.polygons.setdefault(poly_group_name, [])
            self.polygons[poly_group_name] += poly_group
        for boundary_name, boundary in other.boundary_nodes.items():
            self.boundary_nodes.setdefault(boundary_name, [])
            self.boundary_nodes[boundary_name] += boundary
        return self

    def __add__(self, other: Mesh) -> Mesh:
        msh = self.copy()
        msh += other
        return msh

    def __getitem__(self, item: str) -> Mesh:
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
    @staticmethod
    def _find_duplicates(nodes: list[Vertex]) -> dict[Vertex, Vertex]:
        node_lst = [p.position for p in nodes]
        duplicates = euklid.mesh.find_duplicates(node_lst, Vertex.dmin)
        duplicates_dct = {}

        for node1_id, node2_id in duplicates:
            node1 = nodes[node1_id]
            node2 = nodes[node2_id]

            if node1 not in duplicates_dct and node1 is not node2:
                duplicates_dct[node2] = node1
                
        return duplicates_dct

    def delete_duplicates(self, boundaries: list[str]=None) -> Mesh:
        """
        :param boundaries: list of boundary names to be joined (None->all)
        :return: Mesh (self)
        """

        _boundaries = boundaries or self.boundary_nodes.keys()
        for name in _boundaries:
            if name not in self.boundary_nodes:
                raise ValueError()
        
        replace_dict = {}
        all_boundary_nodes: list[Vertex] = sum([self.boundary_nodes[name] for name in _boundaries], [])

        replace_dict = self._find_duplicates(all_boundary_nodes)

        for node, replacement in replace_dict.items():
            replacement.attributes.update(node.attributes)

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

        for polygon in self.get_all_polygons():
            for i, node in enumerate(polygon):
                if node in replace_dict:
                    polygon[i] = replace_dict[node]

        # delete duplicated nodes in every element
        for group_name, poly_group in self.polygons.items():
            for i, polygon in enumerate(poly_group):
                poly_set = set(polygon)
                new_polygon = Polygon([node for node in polygon if node in poly_set])
                new_polygon.attributes = polygon.attributes
                self.polygons[group_name][i] = new_polygon

        vertices = self.vertices
        for boundary_name in _boundaries:
            for i, node in enumerate(self.boundary_nodes[boundary_name]):
                if node not in vertices:
                    logger.warning(f"uiuiui, {node} in replace dict is not in vertices")
        return self

    def polygon_size(self) -> tuple[float, float, float]:
        """Get the min / max / avg polygon size"""
        polygons = self.get_all_polygons()

        polygon_sizes = [poly.area for poly in polygons if len(poly) in (3, 4)]

        return min(polygon_sizes), max(polygon_sizes), sum(polygon_sizes)/len(polygon_sizes)
