import euklid
from collections.abc import Iterator, Sized
from meshpy.triangle import MeshInfo
import meshpy._internals as internals

class Triangle(Sized):
    attributes: dict
    nodes: tuple[int, int, int]

    def __init__(self, lst: tuple[int, int, int], name: str=""):
        self.nodes = lst
        self.attributes = {
            "name": name
        }
    
    def __iter__(self) -> Iterator[int]:
        return self.nodes.__iter__()
    
    def __len__(self) -> int:
        return 3


class TriMesh:
    def __init__(self, mesh_info: MeshInfo, name: str=""):
        self.points = [euklid.vector.Vector2D(p) for p in mesh_info.points]

        self.elements = [
            Triangle(v, name) for v in mesh_info.elements
        ]

VectorList = list[tuple[float, float]]

class Triangulation:
    meshpy_keep_boundary = True
    meshpy_planar_straight_line_graph = True
    meshpy_max_area: float | None = None
    meshpy_incremental_algorithm = True
    meshpy_quality_mesh = True

    name: str = ""

    def __init__(self, vertices: VectorList, boundary: list[list[int]]=None, holes: VectorList | None=None):
        self.vertices = vertices
        self.boundary = boundary
        self.holes = holes

    @staticmethod
    def get_segments(polyline: list[int]) -> list[tuple[int, int]]:
        segments = []
        for i in range(len(polyline)-1):
            segments.append((polyline[i], polyline[i+1]))

        return segments

    def _get_triangle_options(self) -> str:
        opts = "Qz"  # quiet and start numbering from zero

        if self.meshpy_keep_boundary:
            opts += "Y"

        if self.meshpy_quality_mesh:
            opts += "q"

        if self.meshpy_incremental_algorithm:
            opts += "i"

        if self.meshpy_planar_straight_line_graph:
            opts += "p"

        if self.meshpy_max_area is not None:
            opts += "a"
            opts += f"{self.meshpy_max_area:f}"

        return opts

    def triangulate(self, options: str | None=None) -> TriMesh:
        if options is None:
            options = self._get_triangle_options()
        mesh_info = MeshInfo()
        mesh_info.set_points(self.vertices)

        if self.boundary is not None:
            segments = []
            for b in self.boundary:
                segments += self.get_segments(b)
            mesh_info.set_facets(segments)

        if self.holes is not None:
            mesh_info.set_holes(self.holes)

        try:
            import locale
        except ImportError:
            use_locale = False
        else:
            use_locale = True
            prev_num_locale = locale.getlocale(locale.LC_NUMERIC)
            locale.setlocale(locale.LC_NUMERIC, "C")

        try:
            mesh = MeshInfo()
            internals.triangulate(options, mesh_info, mesh, MeshInfo(), None)
        finally:
            # restore previous locale if we've changed it
            if use_locale:
                locale.setlocale(locale.LC_NUMERIC, prev_num_locale)

        return TriMesh(mesh, self.name)
