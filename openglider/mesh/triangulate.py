"""
Triangulation module for 2D Delaunay triangulation with constrained boundaries.

This module provides a triangulation interface that uses the PolyTri library
to perform Delaunay triangulation on 2D point sets with support for constrained
boundaries and hole removal. It replaces the previous meshpy dependency while
maintaining a compatible API.

The main classes are:
    - Triangulation: Main triangulation class for creating triangulated meshes
    - TriangulationResult: Container for triangulation results

Example:
    >>> import numpy as np
    >>> from openglider.mesh.triangulate import Triangulation
    >>>
    >>> # Create a simple triangle
    >>> vertices = np.array([[0, 0], [1, 0], [0.5, 1]])
    >>> tri = Triangulation(vertices)
    >>> result = tri.triangulate()
    >>>
    >>> # Access results
    >>> print(f"Vertices: {result.points}")
    >>> print(f"Triangles: {result.elements}")
"""
import numpy as np
from polytri import PolyTri


class TriangulationResult(object):
    """
    Result object returned by triangulation operations.
    
    This class provides a meshpy-compatible interface for triangulation results,
    containing the points and triangle elements of the triangulated mesh.
    
    Attributes:
        points (numpy.ndarray): Array of 2D or 3D points (vertices) used in the triangulation.
            Shape: (N, 2) or (N, 3) where N is the number of vertices.
        elements (list): List of triangles, where each triangle is a list or array
            of 3 vertex indices. Each index refers to a point in the `points` array.
    
    Example:
        >>> result = triangulation.triangulate()
        >>> print(f"Number of vertices: {len(result.points)}")
        >>> print(f"Number of triangles: {len(result.elements)}")
    """
    def __init__(self, points, elements):
        """
        Initialize a TriangulationResult object.
        
        Args:
            points (array-like): Array of points (vertices) used in triangulation.
            elements (list): List of triangles, where each triangle contains 3 vertex indices.
        """
        self.points = points
        self.elements = elements


class Triangulation(object):
    """
    Delaunay triangulation with constrained boundaries and hole support.
    
    This class provides triangulation functionality using the PolyTri library,
    which replaces the previous meshpy dependency. It supports constrained
    boundaries and hole removal for complex 2D geometries.
    
    The triangulation can handle:
    - Constrained boundaries (outer boundary and holes)
    - Delaunay triangulation for quality meshes
    - Non-convex geometries
    
    Attributes:
        vertices (numpy.ndarray): Array of input vertices (2D or 3D points).
        boundary (list, optional): List of boundary definitions. Each boundary is
            a list of vertex indices forming a closed loop. The first boundary
            is the outer boundary, subsequent boundaries are holes.
        holes (bool): Whether to remove triangles inside holes. Default: False.
    
    Example:
        >>> # Simple triangulation without boundaries
        >>> vertices = np.array([[0, 0], [1, 0], [0.5, 1]])
        >>> tri = Triangulation(vertices)
        >>> result = tri.triangulate()
        
        >>> # Triangulation with boundary
        >>> vertices = np.array([[0, 0], [1, 0], [1, 1], [0, 1]])
        >>> boundary = [[0, 1, 2, 3, 0]]  # Square boundary
        >>> tri = Triangulation(vertices, boundary=boundary)
        >>> result = tri.triangulate()
        
        >>> # Triangulation with holes
        >>> outer_vertices = np.array([[0, 0], [2, 0], [2, 2], [0, 2]])
        >>> hole_vertices = np.array([[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5]])
        >>> all_vertices = np.vstack([outer_vertices, hole_vertices])
        >>> boundary = [
        ...     [0, 1, 2, 3, 0],  # Outer boundary
        ...     [4, 5, 6, 7, 4]   # Hole boundary
        ... ]
        >>> tri = Triangulation(all_vertices, boundary=boundary, holes=True)
        >>> result = tri.triangulate()
    """
    def __init__(self, vertices, boundary=None, holes=None):
        """
        Initialize a Triangulation object.
        
        Args:
            vertices (array-like): Array of 2D or 3D points to triangulate.
                Shape should be (N, 2) or (N, 3) where N is the number of vertices.
            boundary (list, optional): List of boundary definitions. Each boundary
                is a list of vertex indices forming a closed loop. The first boundary
                is treated as the outer boundary, subsequent boundaries are holes.
                If None, no boundaries are constrained.
            holes (bool, optional): Whether to remove triangles inside holes.
                Only relevant if multiple boundaries are provided. Default: False.
        
        Note:
            The first boundary is automatically reversed to ensure correct orientation
            for the triangulation algorithm.
        """
        self.vertices = np.array(vertices)
        self.boundary = boundary
        self.holes = bool(holes)

        # Reverse first boundary for correct orientation
        if self.boundary is not None and len(self.boundary) > 0:
            self.boundary[0] = self.boundary[0][::-1]

    @staticmethod
    def get_segments(polyline):
        """
        Convert a polyline (list of vertex indices) into segments (edge pairs).
        
        This method takes a polyline defined by vertex indices and converts it
        into a list of segments, where each segment is a pair of consecutive
        vertex indices representing an edge.
        
        Args:
            polyline (list): List of vertex indices forming a polyline.
                The polyline can be open or closed (if first and last index are the same).
        
        Returns:
            list: List of segments, where each segment is [start_index, end_index].
                For a polyline with N points, returns N-1 segments.
        
        Example:
            >>> # Open polyline
            >>> polyline = [0, 1, 2, 3]
            >>> segments = Triangulation.get_segments(polyline)
            >>> # Returns: [[0, 1], [1, 2], [2, 3]]
            
            >>> # Closed polyline
            >>> polyline = [0, 1, 2, 0]
            >>> segments = Triangulation.get_segments(polyline)
            >>> # Returns: [[0, 1], [1, 2], [2, 0]]
        """
        segments = []
        for i in range(len(polyline) - 1):
            segments.append([polyline[i], polyline[i + 1]])
        return segments


    def triangulate(self, options=None):
        """
        Perform Delaunay triangulation on the input vertices.
        
        This method creates a triangulation of the input vertices using the PolyTri
        library. If boundaries are specified, they are constrained in the triangulation.
        If holes are enabled and multiple boundaries are provided, triangles inside
        the hole boundaries are removed.
        
        Args:
            options (str, optional): Triangulation options string (for compatibility
                with meshpy interface). Currently not used, but kept for API compatibility.
                Default: None.
        
        Returns:
            TriangulationResult: Object containing the triangulation results with:
                - points: Array of vertices (same as input vertices)
                - elements: List of triangles, where each triangle is a list of 3 vertex indices
        
        Raises:
            ValueError: If the input vertices are invalid or insufficient for triangulation.
            TypeError: If boundaries are provided in an invalid format.
        
        Example:
            >>> vertices = np.array([[0, 0], [1, 0], [0.5, 1], [0.5, 0.5]])
            >>> boundary = [[0, 1, 2, 0]]
            >>> tri = Triangulation(vertices, boundary=boundary)
            >>> result = tri.triangulate()
            >>> print(f"Triangles: {result.elements}")
            >>> print(f"Vertices: {result.points}")
        
        Note:
            - The triangulation uses Delaunay criterion for quality meshes
            - Boundary constraints are enforced during triangulation
            - Hole removal is performed after triangulation if enabled
            - Triangle indices refer to the original vertex array order
        """
        triangulation = PolyTri(
            self.vertices,
            boundaries=self.boundary,
            delaunay=True,
            holes=self.holes,
            border=[]
        )

        result = TriangulationResult(
            points=self.vertices,
            elements=triangulation.get_triangles()
        )

        return result
