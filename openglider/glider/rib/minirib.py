from openglider.airfoil import Profile3D
from openglider.mesh import Mesh, triangulate
import numpy as np


class MiniRib:
    def __init__(
        self,
        yvalue,
        intrados_start=0.8,
        extrados_start=0.75,
        end_distance=0.02,  # Fixed distance from TE in meters (2cm default)
        transition_length=0.05,  # Length of progressive transition zone (in chord %)
        name="minirib",
        # Hole parameters
        num_holes=0,
        hole_width=0.5,  # Width ratio (0-1 of minirib width)
        hole_height=0.7,  # Height ratio (0-1 of minirib height)  
        hole_shape=0,  # 0=Ellipse, 1=Rounded Rectangle
        hole_corner_radius=0.25,  # Corner radius ratio for rounded rectangles
        hole_max_pos=0.9,  # Max position (0-1, limits holes to avoid thin tip)
    ):
        self.y_value = yvalue
        self.intrados_start = intrados_start
        self.extrados_start = extrados_start
        self.end_distance = end_distance  # in meters (e.g., 0.02 = 2cm)
        self.transition_length = transition_length  # e.g., 0.05 = 5% chord
        self.name = name
        # Hole parameters
        self.num_holes = num_holes
        self.hole_width = hole_width
        self.hole_height = hole_height
        self.hole_shape = hole_shape
        self.hole_corner_radius = hole_corner_radius
        self.hole_max_pos = hole_max_pos

    def get_end_percentage(self, chord):
        """
        Calculate end percentage based on fixed distance from TE.
        """
        if chord > 0:
            # Convert fixed distance to percentage of chord
            end_pct = 1.0 - (self.end_distance / chord)
            return max(0.0, min(1.0, end_pct))
        return 0.99  # Fallback

    def function(self, x, chord=None):
        """
        Returns ballooning factor:
        0 = Constrained (Rib shape)
        1 = Unconstrained (Ballooned shape)
        Values between 0-1 for progressive transition (smooth S-curve)
        
        x is signed coordinate from Profile2D:
        x < 0: Upper / Extrados
        x >= 0: Lower / Intrados
        
        chord: used to calculate end position from fixed distance
        """
        import math
        
        # Calculate end percentage from fixed distance
        end_pct = self.get_end_percentage(chord) if chord else 0.99
        
        if x < 0:  # Upper / Extrados
            pos = -x
            start = self.extrados_start
            
            if pos > end_pct:
                return 1.0  # Beyond end: fully ballooned
            elif pos >= start:
                # In the transition zone at the start?
                if self.transition_length > 0 and pos < start + self.transition_length:
                    # Smooth S-curve transition using cosine
                    t = (pos - start) / self.transition_length
                    # Use cosine for asymptotic curve: 0.5 * (1 + cos(pi * t))
                    return 0.5 * (1.0 + math.cos(math.pi * t))
                return 0.0  # Constrained zone
            else:
                return 1.0  # Before start: fully ballooned
        else:  # Lower / Intrados
            pos = x
            start = self.intrados_start
            
            if pos > end_pct:
                return 1.0  # Beyond end: fully ballooned
            elif pos >= start:
                # In the transition zone at the start?
                if self.transition_length > 0 and pos < start + self.transition_length:
                    # Smooth S-curve transition using cosine
                    t = (pos - start) / self.transition_length
                    # Use cosine for asymptotic curve: 0.5 * (1 + cos(pi * t))
                    return 0.5 * (1.0 + math.cos(math.pi * t))
                return 0.0  # Constrained zone
            else:
                return 1.0  # Before start: fully ballooned

    def get_3d(self, cell):
        """
        Get the 3D profile for the mini rib.
        Generates points uniformly distributed within the mini rib range,
        with progressive ballooning in the transition zone.
        """
        import numpy as np
        
        rib1 = cell.rib1
        rib2 = cell.rib2
        y = self.y_value
        
        # Interpolate chord for fixed distance calculations
        chord = rib1.chord * (1 - y) + rib2.chord * y
        
        # Calculate end percentage from fixed distance
        end_pct = self.get_end_percentage(chord)
        
        # Number of points per side (extrados/intrados)
        num_points = 40
        
        # Generate x_values to form a closed loop:
        # Extrados: from start toward trailing edge (negative x values), but stop just before TE
        # Then add a single shared TE point (average of upper/lower)
        # Intrados: from just after TE back toward start (positive x values)
        extrados_x = np.linspace(-self.extrados_start, -end_pct, num_points)[:-1]  # Exclude last (TE)
        intrados_x = np.linspace(end_pct, self.intrados_start, num_points)[1:]    # Exclude first (TE)
        
        # Add a special marker for the shared TE point (we'll handle it separately)
        # x=0 at end_pct means "use trailing edge point"
        te_x = end_pct  # Trailing edge x position (will use midpoint of upper/lower)
        
        # Combine: extrados (toward TE), TE point, intrados (back from TE)
        x_values_extrados = list(extrados_x)
        x_values_intrados = list(intrados_x)
        
        # Get the profiles - note that profile_2d and profile_3d have the same number of points
        # and the same point ordering, so we can use profile_2d(x) as index into profile_3d
        prof2d_1 = rib1.profile_2d
        prof2d_2 = rib2.profile_2d
        prof3d_1 = rib1.profile_3d
        prof3d_2 = rib2.profile_3d
        
        # Get ballooned midrib - same point count as profile_3d
        ballooned_midrib = cell.basic_cell.midrib(y, ballooning=True)
        
        def get_point_3d(x):
            """Helper to get a 3D point at position x with ballooning."""
            fakt = self.function(x, chord=chord)
            ik = prof2d_1(x)
            pt1 = prof3d_1[ik]
            pt2 = prof3d_2[ik]
            pt_unballooned = pt1 * (1 - y) + pt2 * y
            pt_ballooned = ballooned_midrib[ik]
            return pt_unballooned + fakt * (pt_ballooned - pt_unballooned)
        
        # Build 3D points: extrados, then TE point, then intrados
        points_3d = []
        
        # Extrados points
        for x in x_values_extrados:
            try:
                points_3d.append(get_point_3d(x))
            except Exception as e:
                continue
        
        # Trailing edge points: add BOTH upper and lower to create flat truncated edge
        # (not average, which would create a pointed tip)
        try:
            pt_upper = get_point_3d(-te_x)  # Extrados at TE position
            pt_lower = get_point_3d(te_x)   # Intrados at TE position
            points_3d.append(pt_upper)  # End of extrados at TE
            points_3d.append(pt_lower)  # Start of intrados at TE
        except Exception as e:
            pass
        
        # Intrados points
        for x in x_values_intrados:
            try:
                points_3d.append(get_point_3d(x))
            except Exception as e:
                continue
        
        return Profile3D(points_3d)

    def get_2d_shape(self, cell):
        """
        Get the 2D profile shape for the mini rib.
        Includes transition zone with ballooning:
        - Front: ballooned thickness (wider)
        - Transition: progressively thinner
        - Back: exact profile thickness (flat)
        """
        from openglider.vector import PolyLine2D
        import numpy as np
        
        rib1 = cell.rib1
        rib2 = cell.rib2
        y = self.y_value
        
        # Interpolate chord
        chord = rib1.chord * (1 - y) + rib2.chord * y
        
        # Calculate end percentage from fixed distance
        end_pct = self.get_end_percentage(chord)
        
        # Number of points per side
        num_points = 40
        
        # Generate x_values to form a closed loop (same as get_3d):
        # Extrados: from start toward TE (exclude last point at TE)
        # Intrados: from TE back toward start (exclude first point at TE)
        extrados_x = np.linspace(-self.extrados_start, -end_pct, num_points)[:-1]
        intrados_x = np.linspace(end_pct, self.intrados_start, num_points)[1:]
        te_x = end_pct  # Trailing edge x position
        
        x_values_extrados = list(extrados_x)
        x_values_intrados = list(intrados_x)
        
        # Get the flat 2D profile for interpolation
        prof_2d = rib1.profile_2d
        
        # Get the 3D ballooned midrib and flatten it for 2D ballooning effect
        try:
            midrib_3d = cell.basic_cell.midrib(y, ballooning=True)
            midrib_flat = midrib_3d.flatten()
            has_ballooned = True
        except Exception as e:
            has_ballooned = False
        
        def get_point_2d(x):
            """Helper to get a 2D point at position x with ballooning."""
            ik = prof_2d(x)
            pt_flat = np.array(prof_2d[ik]) * chord
            fakt = self.function(x, chord=chord)
            if fakt > 0 and has_ballooned:
                pt_ballooned = np.array(midrib_flat[ik])
                return pt_flat + fakt * (pt_ballooned - pt_flat)
            return pt_flat
        
        # Build 2D points: extrados, then TE point, then intrados
        points_2d = []
        
        # Extrados points
        for x in x_values_extrados:
            try:
                points_2d.append(get_point_2d(x))
            except Exception as e:
                continue
        
        # Trailing edge points: add BOTH upper and lower to create flat truncated edge
        # (not average, which would create a pointed tip)
        try:
            pt_upper = get_point_2d(-te_x)  # Extrados at TE position
            pt_lower = get_point_2d(te_x)   # Intrados at TE position
            points_2d.append(pt_upper)  # End of extrados at TE
            points_2d.append(pt_lower)  # Start of intrados at TE
        except Exception as e:
            pass
        
        # Intrados points
        for x in x_values_intrados:
            try:
                points_2d.append(get_point_2d(x))
            except Exception as e:
                continue
        
        if len(points_2d) < 2:
            return None
        
        # Filter out duplicate consecutive points
        filtered_points = [points_2d[0]]
        for pt in points_2d[1:]:
            if not np.allclose(pt, filtered_points[-1], atol=1e-10):
                filtered_points.append(pt)
        
        if len(filtered_points) < 2:
            return None
        
        return PolyLine2D(filtered_points)

    def get_flattened(self, cell, close=True):
        """Get flattened 2D profile using exact airfoil shape."""
        from openglider.vector import PolyLine2D
        
        shape = self.get_2d_shape(cell)
        if shape is None or len(shape.data) < 2:
            return PolyLine2D([])
        
        if close and len(shape.data) > 2:
            # Close the curve by adding the first point at the end
            closed_data = list(shape.data) + [shape.data[0]]
            return PolyLine2D(closed_data)
        return shape

    def get_flattened_with_allowance(self, cell, allowance=0.006):
        """Get flattened 2D profile with seam allowance as outer cut line."""
        from openglider.vector import PolyLine2D
        import numpy as np
        
        shape = self.get_2d_shape(cell)
        if shape is None or len(shape.data) < 3:
            return None, None
        
        inner = PolyLine2D(shape.data)
        
        # Close the inner curve
        inner_closed = PolyLine2D(list(inner.data) + [inner.data[0]])
        
        # Create outer curve with proper parallel offset
        # Calculate perpendicular offset at each point
        points = list(shape.data)
        n = len(points)
        outer_points = []
        
        for i in range(n):
            # Get previous and next points (with wrapping for closed curve)
            prev_pt = np.array(points[(i - 1) % n])
            curr_pt = np.array(points[i])
            next_pt = np.array(points[(i + 1) % n])
            
            # Calculate tangent vectors
            t1 = curr_pt - prev_pt
            t2 = next_pt - curr_pt
            
            # Calculate perpendicular normals (rotate 90 degrees)
            # For 2D: perpendicular of (x, y) is (-y, x) for left turn
            n1 = np.array([-t1[1], t1[0]])
            n2 = np.array([-t2[1], t2[0]])
            
            # Normalize
            len1 = np.linalg.norm(n1)
            len2 = np.linalg.norm(n2)
            if len1 > 1e-10:
                n1 = n1 / len1
            if len2 > 1e-10:
                n2 = n2 / len2
            
            # Average normal at this point
            avg_normal = (n1 + n2) / 2.0
            len_avg = np.linalg.norm(avg_normal)
            if len_avg > 1e-10:
                avg_normal = avg_normal / len_avg
            
            # Offset point
            outer_pt = curr_pt + avg_normal * allowance
            outer_points.append(outer_pt)
        
        outer_closed = PolyLine2D(outer_points + [outer_points[0]])
        
        return inner_closed, outer_closed

    def get_hole_contours_2d(self, cell):
        """
        Get hole contours as PolyLine2D objects for 2D export.
        Returns list of PolyLine2D objects representing the holes.
        """
        from openglider.vector import PolyLine2D
        
        if self.num_holes <= 0:
            return []
        
        holes_data = self.generate_holes(cell)
        hole_contours = []
        
        for hole_pts, hole_center in holes_data:
            if len(hole_pts) >= 3:
                # Convert to PolyLine2D (already closed from generate_holes)
                hole_contours.append(PolyLine2D(list(hole_pts)))
        
        return hole_contours

    def generate_holes(self, cell):
        """
        Generate hole contours for the minirib in 2D.
        Holes adapt to the local height of the minirib at each position.
        Returns list of (hole_vertices, hole_center) tuples.
        """
        if self.num_holes <= 0:
            return []
        
        shape_2d = self.get_2d_shape(cell)
        if shape_2d is None or len(shape_2d.data) < 3:
            return []
        
        points = np.array(shape_2d.data)
        
        # Calculate bounding box of minirib
        min_x, min_y = points.min(axis=0)
        max_x, max_y = points.max(axis=0)
        total_width = max_x - min_x
        
        if total_width <= 0:
            return []
        
        # Helper to find local height at a given x position
        def get_local_height_at_x(x_pos):
            """Find the top and bottom y values at a specific x position."""
            # Find points that bracket this x position
            y_top = min_y
            y_bottom = max_y
            
            n = len(points)
            for i in range(n):
                p1 = points[i]
                p2 = points[(i + 1) % n]
                
                # Check if this edge crosses the x position
                if (p1[0] <= x_pos <= p2[0]) or (p2[0] <= x_pos <= p1[0]):
                    if abs(p2[0] - p1[0]) > 1e-10:
                        # Linear interpolation
                        t = (x_pos - p1[0]) / (p2[0] - p1[0])
                        y_at_x = p1[1] + t * (p2[1] - p1[1])
                        y_top = max(y_top, y_at_x)
                        y_bottom = min(y_bottom, y_at_x)
            
            return y_bottom, y_top
        
        holes = []
        
        # Calculate hole positions evenly distributed along the usable width
        # Use hole_max_pos to limit the zone (avoid thin tip)
        max_pos = getattr(self, 'hole_max_pos', 0.9)
        usable_end_x = min_x + total_width * max_pos
        margin = total_width * 0.05  # 5% margin from leading edge
        usable_width = usable_end_x - (min_x + margin)
        
        if usable_width <= 0:
            return []
        
        if self.num_holes == 1:
            hole_positions = [min_x + margin + usable_width / 2]
        else:
            hole_positions = [min_x + margin + usable_width * i / (self.num_holes - 1) 
                              for i in range(self.num_holes)]
        
        for hx in hole_positions:
            # Get local height at this x position
            y_bottom, y_top = get_local_height_at_x(hx)
            local_height = y_top - y_bottom
            
            if local_height <= 0.001:  # Skip if too thin
                continue
            
            # Center y position
            hy = (y_top + y_bottom) / 2
            
            # Hole size based on local height and spacing
            hole_spacing = usable_width / max(1, self.num_holes) if self.num_holes > 1 else usable_width
            hole_w = min(hole_spacing * 0.8, local_height * self.hole_height) * self.hole_width
            hole_h = local_height * self.hole_height * 0.8  # 80% of available height
            
            # Ensure minimum hole size
            if hole_w < 0.001 or hole_h < 0.001:
                continue
            
            hole_pts = self._create_hole_shape(hx, hy, hole_w, hole_h)
            if hole_pts is not None and len(hole_pts) >= 3:
                holes.append((hole_pts, np.array([hx, hy])))
        
        return holes

    def _create_hole_shape(self, cx, cy, w, h, num_points=20):
        """Create a hole shape (ellipse or rounded rectangle) centered at (cx, cy)."""
        if w <= 0 or h <= 0:
            return None
        
        if self.hole_shape == 0:  # Ellipse
            angles = np.linspace(0, 2 * np.pi, num_points + 1)
            points = []
            for angle in angles:
                x = cx + (w / 2) * np.cos(angle)
                y = cy + (h / 2) * np.sin(angle)
                points.append([x, y])
            return np.array(points)
        else:  # Rounded rectangle
            radius = min(w, h) * self.hole_corner_radius
            radius = min(radius, w / 2.0, h / 2.0)
            
            hw = max(0, w / 2.0 - radius)
            hh = max(0, h / 2.0 - radius)
            
            points = []
            num_corner = max(2, num_points // 4)
            
            # Top right
            for angle in np.linspace(0, np.pi/2, num_corner):
                points.append([cx + hw + radius * np.cos(angle), cy + hh + radius * np.sin(angle)])
            # Top left
            for angle in np.linspace(np.pi/2, np.pi, num_corner):
                points.append([cx - hw + radius * np.cos(angle), cy + hh + radius * np.sin(angle)])
            # Bottom left
            for angle in np.linspace(np.pi, 3*np.pi/2, num_corner):
                points.append([cx - hw + radius * np.cos(angle), cy - hh + radius * np.sin(angle)])
            # Bottom right
            for angle in np.linspace(3*np.pi/2, 2*np.pi, num_corner):
                points.append([cx + hw + radius * np.cos(angle), cy - hh + radius * np.sin(angle)])
            
            # Close the polygon
            if len(points) > 0:
                points.append(points[0])
            
            return np.array(points)

    def get_mesh(self, cell, filled=True):
        """Generate mesh for the minirib (without holes - holes are in 2D export only)."""
        profile = self.get_3d(cell)
        points_3d = list(profile.data)
        
        # Robustness checks
        if len(points_3d) < 2:
            return Mesh.from_indexed([], {}, {})
        if filled and len(points_3d) < 3:
            return Mesh.from_indexed([], {}, {})
        
        n = len(points_3d)
        
        if not filled:
            # Just the boundary segments
            segments = [[i, (i + 1) % n] for i in range(n)]
            return Mesh.from_indexed(points_3d, {"rib": segments}, {})
        
        # Simple fan triangulation from centroid (holes are only in 2D export)
        centroid = np.mean(np.array(points_3d), axis=0)
        points_3d.append(centroid)
        centroid_idx = n
        
        triangles = []
        for i in range(n):
            j = (i + 1) % n
            triangles.append([i, j, centroid_idx])
        
        return Mesh.from_indexed(
            points_3d,
            polygons={"ribs": triangles},
            boundaries={self.name: list(range(n))},
        )

    def _get_mesh_with_holes(self, cell):
        """Generate mesh with holes using 2D triangulation."""
        shape_2d = self.get_2d_shape(cell)
        if shape_2d is None or len(shape_2d.data) < 3:
            return Mesh.from_indexed([], {}, {})
        
        # Get 2D boundary vertices
        boundary_2d = list(shape_2d.data)
        n_boundary = len(boundary_2d)
        
        # Close the boundary if needed
        if not np.allclose(boundary_2d[0], boundary_2d[-1]):
            boundary_2d.append(boundary_2d[0])
            
        vertices_2d = list(boundary_2d[:-1])  # Without closing point
        n = len(vertices_2d)
        boundary = [[list(range(n)) + [0]]]
        
        # Generate holes
        holes_data = self.generate_holes(cell)
        hole_centers = []
        
        for hole_pts, hole_center in holes_data:
            start_idx = len(vertices_2d)
            hole_verts = list(hole_pts[:-1]) if len(hole_pts) > 0 else []  # Remove closing point
            if len(hole_verts) < 3:
                continue
            hole_indices = list(range(len(hole_verts))) + [0]
            vertices_2d.extend(hole_verts)
            boundary.append([start_idx + i for i in hole_indices])
            hole_centers.append(hole_center.tolist())
        
        if len(vertices_2d) < 3:
            return Mesh.from_indexed([], {}, {})
        
        # Triangulate in 2D
        try:
            tri = triangulate.Triangulation(vertices_2d, boundary[0] + boundary[1:] if len(boundary) > 1 else boundary[0], hole_centers if hole_centers else None)
            mesh_2d = tri.triangulate()
            
            if not hasattr(mesh_2d, 'points') or len(mesh_2d.points) == 0:
                return self._fallback_mesh(cell)
            
            # Map 2D mesh points to 3D
            mesh_pts_2d = list(mesh_2d.points)
            triangles = list(mesh_2d.elements)
            
            # Get 3D profile for mapping
            profile_3d = self.get_3d(cell)
            points_3d_boundary = list(profile_3d.data)
            
            # For boundary points, use the 3D profile directly
            # For interior points, interpolate
            mesh_pts_3d = []
            for i, pt_2d in enumerate(mesh_pts_2d):
                if i < n:
                    # Boundary point - use 3D profile directly
                    mesh_pts_3d.append(points_3d_boundary[i])
                else:
                    # Interior point - approximate by finding closest boundary and interpolating
                    # Simple approach: use centroid's z coordinate
                    centroid_3d = np.mean(np.array(points_3d_boundary), axis=0)
                    # Scale the 2D point proportionally
                    mesh_pts_3d.append([pt_2d[0], pt_2d[1], centroid_3d[2] if len(centroid_3d) > 2 else 0])
            
            return Mesh.from_indexed(
                mesh_pts_3d,
                polygons={"ribs": triangles},
                boundaries={self.name: list(range(n))},
            )
        except Exception as e:
            print(f"Minirib triangulation failed: {e}")
            return self._fallback_mesh(cell)

    def _fallback_mesh(self, cell):
        """Fallback to simple fan triangulation if holes fail."""
        profile = self.get_3d(cell)
        points_3d = list(profile.data)
        n = len(points_3d)
        
        if n < 3:
            return Mesh.from_indexed([], {}, {})
        
        centroid = np.mean(np.array(points_3d), axis=0)
        points_3d.append(centroid)
        centroid_idx = n
        
        triangles = []
        for i in range(n):
            j = (i + 1) % n
            triangles.append([i, j, centroid_idx])
        
        return Mesh.from_indexed(
            points_3d,
            polygons={"ribs": triangles},
            boundaries={self.name: list(range(n))},
        )

    def __json__(self):
        return {
            "yvalue": self.y_value,
            "intrados_start": self.intrados_start,
            "extrados_start": self.extrados_start,
            "end_distance": self.end_distance,
            "transition_length": self.transition_length,
            "name": self.name,
            "num_holes": self.num_holes,
            "hole_width": self.hole_width,
            "hole_height": self.hole_height,
            "hole_shape": self.hole_shape,
            "hole_corner_radius": self.hole_corner_radius,
            "hole_max_pos": self.hole_max_pos,
        }
