from __future__ import division
from __future__ import absolute_import
from meshpy.triangle import MeshInfo
import numpy as np

try:
    import meshpy._triangle as internals
    # old API
    # TODO: Remove??
except ImportError:
    import meshpy._internals as internals
    # new API (pybind11)


class Triangulation(object):
    meshpy_keep_boundary = True
    meshpy_planar_straight_line_graph = True
    meshpy_restrict_area = True
    meshpy_max_area = None
    meshpy_incremental_algorithm = True
    meshpy_quality_mesh = True

    def __init__(self, vertices, boundary=None, holes=None):
        self.vertices = vertices
        self.boundary = boundary
        self.holes = holes

    @staticmethod
    def get_segments(polyline):
        segments = []
        for i in range(len(polyline) - 1):
            segments.append([polyline[i], polyline[i + 1]])

        return segments

    def _get_triangle_options(self):
        opts = "Qz"  # quiet and start numbering from zero

        if self.meshpy_keep_boundary:
            opts += "Y"

        if self.meshpy_quality_mesh:
            opts += "q"

        if self.meshpy_incremental_algorithm:
            opts += "i"

        if self.meshpy_planar_straight_line_graph:
            opts += "p"

        if self.meshpy_restrict_area:
            opts += "a"
            if self.meshpy_max_area is not None:
                opts += "{:f}".format(self.meshpy_max_area)

        return opts

    def _validate_data(self):
        """Validate input data before passing to meshpy to avoid crashes."""
        if not self.vertices or len(self.vertices) < 3:
            print("Triangulation warning: Not enough vertices")
            return False
        
        # Check for NaN or Inf values
        for i, v in enumerate(self.vertices):
            if not np.isfinite(v[0]) or not np.isfinite(v[1]):
                print(f"Triangulation warning: Invalid vertex at index {i}: {v}")
                return False
        
        # Check hole centers are valid
        if self.holes:
            for i, h in enumerate(self.holes):
                if not np.isfinite(h[0]) or not np.isfinite(h[1]):
                    print(f"Triangulation warning: Invalid hole center at index {i}: {h}")
                    return False
        
        return True

    def triangulate(self, options=None):
        if options is None:
            options = self._get_triangle_options()
        
        # Validate data first
        if not self._validate_data():
            print("Triangulation: Skipping due to invalid data")
            # Return empty mesh
            empty_mesh = MeshInfo()
            return empty_mesh
            
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
        except Exception as e:
            print(f"Triangulation error: {e}")
            print(f"  Vertices count: {len(self.vertices)}")
            print(f"  Boundary count: {len(self.boundary) if self.boundary else 0}")
            print(f"  Holes count: {len(self.holes) if self.holes else 0}")
            mesh = MeshInfo()  # Return empty mesh on error
        finally:
            # restore previous locale if we've changed it
            if use_locale:
                locale.setlocale(locale.LC_NUMERIC, prev_num_locale)

        return mesh
