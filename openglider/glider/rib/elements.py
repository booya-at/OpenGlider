#! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.
import numpy as np
import math

from openglider.lines import Node
from openglider.vector.polygon import Circle
from openglider.vector.polyline import PolyLine2D
from openglider.vector.functions import set_dimension
from openglider.vector.spline import Bezier
from openglider.vector import norm
from openglider.vector.transformation import Rotation, Translation, Scale


class RigidFoil(object):
    def __init__(self, start=-0.1, end=0.1, distance=0.005, circle_radius=0.03):
        self.start = start
        self.end = end
        self.distance = distance
        self.circle_radius = circle_radius
        # self.func = lambda x: distance

    def func(self, pos):
        dsq = None
        if -0.05 <= pos - self.start < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + self.start - pos) ** 2
        if -0.05 <= self.end - pos < self.circle_radius:
            dsq = self.circle_radius**2 - (self.circle_radius + pos - self.end) ** 2

        if dsq is not None:
            dsq = max(dsq, 0)
            return self.distance + (self.circle_radius - np.sqrt(dsq)) * 0.35
        return self.distance

    def __json__(self):
        return {"start": self.start, "end": self.end, "distance": self.distance}

    def get_3d(self, rib):
        return [rib.align(p, scale=False) for p in self.get_flattened(rib)]

    def get_length(self, rib):
        return self.get_flattened(rib).get_length()

    def get_flattened(self, rib):
        flat = PolyLine2D(self._get_flattened(rib))
        flat.check()
        return flat

    def _get_flattened(self, rib):
        max_segment = 0.005  # 5mm
        profile = rib.profile_2d
        profile_normvectors = PolyLine2D(profile.normvectors)

        start = profile(self.start)
        end = profile(self.end)

        point_range = []
        last_node = None
        for p in profile[start:end]:
            sign = -1 if p[1] > 0 else +1

            if last_node is not None:
                diff = norm(p - last_node) * rib.chord
                if diff > max_segment:
                    segments = int(math.ceil(diff / max_segment))
                    point_range += list(
                        np.linspace(point_range[-1], sign * p[0], segments)
                    )[1:]
                else:
                    point_range.append(sign * p[0])
            else:
                point_range.append(sign * p[0])

            last_node = p

        indices = [profile(x) for x in point_range]

        return [
            (profile[index] - profile_normvectors[index] * self.func(x)) * rib.chord
            for index, x in zip(indices, point_range)
        ]


class FoilCurve(object):
    def __init__(self, front=0, end=0.17):
        self.front = front
        self.end = end

    def get_flattened(self, rib, numpoints=30):
        curve = [
            [self.end, 0.75],
            [self.end - 0.05, 1],
            [self.front, 0],
            [self.end - 0.05, -1],
            [self.end, -0.75],
        ]
        profile = rib.profile_2d

        cp = [profile.align(point) * rib.chord for point in curve]

        return Bezier(cp).interpolation(numpoints)


class GibusArcs(object):
    """
    A Reinforcement, in the shape of an arc, to reinforce attachment points
    """

    def __init__(self, position, size=0.2, material_code=None):
        self.pos = position
        self.size = size
        self.size_abs = False
        self.material_code = material_code or ""

    def __json__(self):
        return {"position": self.pos, "size": self.size}

    def get_3d(self, rib, num_points=10):
        # create circle with center on the point
        gib_arc = self.get_flattened(rib, num_points=num_points)
        return [rib.align([p[0], p[1], 0], scale=False) for p in gib_arc]

    def get_flattened(self, rib, num_points=10):
        # get center point
        profile = rib.profile_2d
        start = profile(self.pos)
        point_1 = profile[start]

        if self.size_abs:
            # reverse scale now
            size = self.size / rib.chord
        else:
            size = self.size
        point_2 = profile.profilepoint(self.pos + size)

        gib_arc = [[], []]  # first, second
        circle = Circle(point_1, point_2).get_sequence()[1:]
        # circle = Polygon(edges=num_points)(point_1, point_2)[0][1:] # todo: is_center -> true
        is_second_run = False

        for i in range(len(circle)):
            if (
                profile.contains_point(circle[i])
                or (i < len(circle) - 1 and profile.contains_point(circle[i + 1]))
                or (i > 1 and profile.contains_point(circle[i - 1]))
            ):
                gib_arc[is_second_run].append(circle[i])
            else:
                is_second_run = True

        # Cut first and last
        gib_arc = gib_arc[1] + gib_arc[0]  # [secondlist] + [firstlist]
        start2 = profile.cut(gib_arc[0], gib_arc[1], start)
        stop = profile.cut(gib_arc[-2], gib_arc[-1], start)
        # Append Profile_List
        gib_arc += profile.get(start2.next()[0], stop.next()[0]).tolist()

        return np.array(gib_arc) * rib.chord


class CellAttachmentPoint(Node):
    def __init__(self, cell, name, cell_pos, rib_pos, force=None):
        super(CellAttachmentPoint, self).__init__(node_type=2)
        self.cell = cell
        self.cell_pos = cell_pos
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {
            "cell": self.cell,
            "cell_pos": self.cell_pos,
            "rib_pos": self.rib_pos,
            "name": self.name,
            "force": self.force,
        }

    def get_position(self):
        ik = self.cell.rib1.profile_2d(self.rib_pos)
        self.vec = self.cell.midrib(self.cell_pos)[ik]
        return self.vec


# Node from lines
class AttachmentPoint(Node):
    def __init__(self, rib, name, rib_pos, force=None):
        super(AttachmentPoint, self).__init__(node_type=2)
        self.rib = rib
        self.rib_pos = rib_pos
        self.name = name
        self.force = force

    def __repr__(self):
        return "<Attachment point '{}' ({})>".format(self.name, self.rib_pos)

    def __json__(self):
        return {
            "rib": self.rib,
            "name": self.name,
            "rib_pos": self.rib_pos,
            "force": self.force,
        }

    def get_position(self):
        self.vec = self.rib.profile_3d[self.rib.profile_2d(self.rib_pos)]
        return self.vec


class RibHole(object):
    def __init__(self, pos, size=0.5, vertical_shift=0.0, rotation=0.0, shape='ellipse', available_height=None, custom_points=None, corner_radius=0.25):
        self.pos = pos
        if isinstance(size, (list, tuple, np.ndarray)):
            self.size = np.array(list(size))
        else:  # float for uniform scaling
            self.size = np.array([size, size])
        self.vertical_shift = vertical_shift
        self.rotation = rotation  # rotation about p1
        self.shape = shape
        self.available_height = available_height
        self.custom_points = custom_points
        self.corner_radius = corner_radius  # Corner radius for rounded rectangles

    def get_3d(self, rib, num=20):
        hole = self.get_points(rib, num=num, available_height=self.available_height)
        return rib.align_all(set_dimension(hole, 3))

    def get_flattened(self, rib, num=80, scale=True):
        points = self.get_points(rib, num, available_height=self.available_height).data
        if scale:
            points *= rib.chord
        return PolyLine2D(points)

    def get_points(self, rib, num=80, available_height=None):
        if self.custom_points is not None:
             # If custom_points are provided, return them directly.
             # They are assumed to be in the rib's local coordinate system (normalized if scale=False context, but RibHole usually handles normalized)
             # Based on apply_holes logic, we will pass normalized coordinates.
             return PolyLine2D(self.custom_points, name=f"{rib.name}-hole")

        prof = rib.profile_2d
        p1 = prof[prof(self.pos)]  # Lower surface point
        p2 = prof[prof(-self.pos)] # Upper surface point

        local_thickness = np.linalg.norm(p2 - p1)

        # Avoid division by zero or errors for very thin profiles
        if local_thickness < 1e-9:
            return PolyLine2D([], name=f"{rib.name}-hole")

        # The caller may pass available_height directly.
        # Prioritize the passed argument, but fall back to the instance attribute.
        effective_ah = available_height if available_height is not None else getattr(self, 'available_height', None)
        height_base = effective_ah if effective_ah is not None else local_thickness

        # Calculate final hole dimensions
        final_width = self.size[0] * height_base
        final_height = self.size[1] * height_base

        # Generate shape centered at (0,0)
        if self.shape == 'ellipse':
            shape_points = []
            for angle in np.linspace(0, 2 * np.pi, num + 1):
                x = final_width / 2 * np.cos(angle)
                y = final_height / 2 * np.sin(angle)
                shape_points.append([x, y])
            shape_poly = np.array(shape_points)
        else:  # rounded rectangle
            shape_poly = self.create_rounded_rectangle(num, final_width, final_height, self.corner_radius)

        # Determine final center position
        # Note: self.vertical_shift is now an absolute shift in the local frame
        final_center = p1 + (p2 - p1) / 2
        final_center[1] += self.vertical_shift * local_thickness

        # Rotate and then translate the shape
        rotation_rad = np.deg2rad(self.rotation)
        rot_matrix = np.array([[np.cos(rotation_rad), -np.sin(rotation_rad)],
                               [np.sin(rotation_rad), np.cos(rotation_rad)]])

        # Apply rotation around shape's origin, then translate to final position
        shape_poly = shape_poly.dot(rot_matrix)
        shape_poly += final_center

        return PolyLine2D(shape_poly, name=f"{rib.name}-hole")

    def create_rounded_rectangle(self, num, width, height, corner_radius=0.005):
        # corner_radius is treated as a ratio of min(width, height)
        # Default 0.25 = 25% of smallest dimension for backward compatibility
        # If corner_radius > 1, assume it was passed as absolute and convert
        if corner_radius > 1.0:
            # Assume it was passed in same units as width/height, convert to ratio
            radius = min(corner_radius, min(width, height) / 2.0)
        else:
            # Treat as ratio
            radius = min(width, height) * corner_radius
        
        if radius < 0: radius = 0
        if radius > width / 2.0: radius = width / 2.0
        if radius > height / 2.0: radius = height / 2.0

        w = max(0.0, width / 2.0 - radius)
        h = max(0.0, height / 2.0 - radius)

        points = []
        num_corner = max(2, num // 4)

        # Top right
        center_x, center_y = w, h
        for angle in np.linspace(0, np.pi/2, num_corner):
            points.append((center_x + radius * np.cos(angle), center_y + radius * np.sin(angle)))

        # Top left
        center_x, center_y = -w, h
        for angle in np.linspace(np.pi/2, np.pi, num_corner):
            points.append((center_x + radius * np.cos(angle), center_y + radius * np.sin(angle)))

        # Bottom left
        center_x, center_y = -w, -h
        for angle in np.linspace(np.pi, 3*np.pi/2, num_corner):
            points.append((center_x + radius * np.cos(angle), center_y + radius * np.sin(angle)))

        # Bottom right
        center_x, center_y = w, -h
        for angle in np.linspace(3*np.pi/2, 2*np.pi, num_corner):
            points.append((center_x + radius * np.cos(angle), center_y + radius * np.sin(angle)))

        # Close the polygon (add first point at the end)
        if len(points) > 0:
            points.append(points[0])

        return np.array(points)

    def get_center(self, rib, scale=True):
        if self.custom_points is not None:
             # Calculate centroid of custom points
             # custom_points is list of [x, y] or numpy arrays
             # Exclude the last point if it closes the loop (same as first point)
             points = [np.array(p) for p in self.custom_points]
             if len(points) > 1:
                 # Check if last point is same as first (closed polygon)
                 if np.linalg.norm(points[0] - points[-1]) < 1e-9:
                     points = points[:-1]
             if len(points) == 0:
                 return np.array([0.0, 0.0])
             center = np.mean(points, axis=0)
             if scale:
                 center = center * rib.chord
             return center

        prof = rib.profile_2d
        p1 = prof[prof(self.pos)]
        p2 = prof[prof(-self.pos)]
        
        local_thickness = np.linalg.norm(p2 - p1)
        
        final_center = p1 + (p2 - p1) / 2
        final_center[1] += self.vertical_shift * local_thickness
        
        if scale:
            final_center *= rib.chord
            
        return final_center

    def __json__(self):
        return {
            "pos": self.pos,
            "size": self.size,
            "vertical_shift": self.vertical_shift,
            "rotation": self.rotation,
            "shape": self.shape,
            "corner_radius": self.corner_radius,
        }

class Mylar(object):
    pass


class RodSleeve(object):
    """
    Rod sleeve (fourreau de jonc) following the airfoil surface.
    
    Used to hold rigid rods that maintain the profile shape in the chord direction.
    Can be placed on extrados or intrados.
    
    Attributes:
        surface: 'extrados' or 'intrados'
        width: Sleeve width in meters (perpendicular to surface)
        offset: Offset from the surface in meters
        start_chord: Start position as chord percentage (0 = leading edge)
        end_chord: End position as chord percentage (1 = trailing edge)
        le_angle: Leading edge escape angle in degrees (0=horizontal right, 90=up, 180=left, 270=down)
        te_angle: Trailing edge escape angle in degrees
        le_length: Leading edge escape length in meters
        te_length: Trailing edge escape length in meters
    """
    
    def __init__(
        self,
        surface='extrados',
        width=0.015,
        offset=0.005,
        start_chord=0.0,
        end_chord=0.85,
        le_angle=0.0,        # Leading edge angle (degrees)
        te_angle=315.0,      # Trailing edge angle (degrees) - default for extrados
        le_length=0.03,      # Leading edge escape length (m)
        te_length=0.08,      # Trailing edge escape length (m)
        material_code=None,
    ):
        self.surface = surface
        self.width = width
        self.offset = offset
        self.start_chord = start_chord
        self.end_chord = end_chord
        self.le_angle = le_angle
        self.te_angle = te_angle
        self.le_length = le_length
        self.te_length = te_length
        self.material_code = material_code or ""
    
    def __json__(self):
        return {
            "surface": self.surface,
            "width": self.width,
            "offset": self.offset,
            "start_chord": self.start_chord,
            "end_chord": self.end_chord,
            "le_angle": self.le_angle,
            "te_angle": self.te_angle,
            "le_length": self.le_length,
            "te_length": self.te_length,
            "material_code": self.material_code,
        }
    
    def get_profile_range(self, profile):
        """
        Get the x-value range for the sleeve based on chord percentages.
        Returns (start_x, end_x) in profile coordinates.
        """
        if self.surface == 'extrados':
            start_x = -self.start_chord
            end_x = -self.end_chord
        else:
            start_x = self.start_chord
            end_x = self.end_chord
        return (start_x, end_x)
    
    def _calculate_normal(self, profile_segment, i, surface):
        """Calculate the perpendicular normal vector at point i."""
        if len(profile_segment) < 2:
            return np.array([0.0, 1.0])
        
        if i == 0:
            tangent = profile_segment[1] - profile_segment[0]
        elif i == len(profile_segment) - 1:
            tangent = profile_segment[-1] - profile_segment[-2]
        else:
            tangent = profile_segment[i + 1] - profile_segment[i - 1]
        
        tangent_len = np.linalg.norm(tangent)
        if tangent_len < 1e-10:
            tangent = np.array([1.0, 0.0])
        else:
            tangent = tangent / tangent_len
        
        if surface == 'extrados':
            normal = np.array([tangent[1], -tangent[0]])
        else:
            normal = np.array([-tangent[1], tangent[0]])
        
        return normal
    
    def _create_smooth_termination_with_width(self, inner_start, outer_start, end_angle_deg, length, 
                                                start_tangent_vec=None, num_points=12):
        """
        Create a smooth termination curve with constant width.
        The curve starts tangent to the main sleeve direction and ends in the specified angle direction.
        
        Args:
            inner_start: Starting point of inner edge (numpy array)
            outer_start: Starting point of outer edge (numpy array)  
            end_angle_deg: FINAL direction angle in degrees (0=right, 90=up, 180=left, 270=down)
            length: Length of the termination
            start_tangent_vec: Optional starting tangent direction. If None, calculated from sleeve orientation.
            num_points: Number of points in the curve
        
        Returns:
            Tuple of (inner_curve, outer_curve) with constant width
        """
        # Calculate center line and width
        center_start = (inner_start + outer_start) / 2
        width = np.linalg.norm(outer_start - inner_start)
        
        # End direction
        end_angle_rad = np.deg2rad(end_angle_deg)
        end_direction = np.array([np.cos(end_angle_rad), np.sin(end_angle_rad)])
        
        # Calculate initial width direction (from inner to outer)
        width_dir = (outer_start - inner_start)
        width_len = np.linalg.norm(width_dir)
        if width_len > 1e-10:
            width_dir_norm = width_dir / width_len
        else:
            width_dir_norm = np.array([0, 1])
        
        # The ONLY valid tangent that preserves inner/outer alignment
        required_tangent = np.array([width_dir_norm[1], -width_dir_norm[0]])
        
        if start_tangent_vec is None:
            start_tangent = required_tangent
        else:
            start_tangent = start_tangent_vec / np.linalg.norm(start_tangent_vec)

        
        # End point: go in end_direction for 'length' distance
        center_end = center_start + end_direction * length
        
        # Control points for cubic Bezier (smooth curve with G1 continuity)
        # First control point: extend from start in start_tangent direction
        # This ensures the curve starts tangent to the main sleeve
        ctrl1 = center_start + start_tangent * length * 0.5
        
        # Second control point: approach end from the end_direction
        # This ensures the curve ends tangent to end_direction
        ctrl2 = center_end - end_direction * length * 0.5
        
        inner_curve = []
        outer_curve = []
        
        # Track previous normal for progressive orientation consistency
        prev_normal = width_dir_norm  # Start with initial width direction
        
        for i in range(num_points):
            t = i / (num_points - 1)
            
            # Cubic Bezier for center line
            center_pt = (
                center_start * (1-t)**3 + 
                ctrl1 * 3 * (1-t)**2 * t + 
                ctrl2 * 3 * (1-t) * t**2 + 
                center_end * t**3
            )
            
            # Calculate tangent at this point (derivative of Bezier)
            tangent = (
                (ctrl1 - center_start) * 3 * (1-t)**2 +
                (ctrl2 - ctrl1) * 6 * (1-t) * t +
                (center_end - ctrl2) * 3 * t**2
            )
            
            tangent_len = np.linalg.norm(tangent)
            if tangent_len > 1e-10:
                tangent = tangent / tangent_len
            else:
                tangent = end_direction
            
            # Normal is perpendicular to tangent
            normal = np.array([-tangent[1], tangent[0]])
            
            # PROGRESSIVE FIX: Compare with PREVIOUS normal, not initial direction
            # This ensures smooth transitions even for large curve turns
            if np.dot(normal, prev_normal) < 0:
                normal = -normal
            
            prev_normal = normal  # Update for next iteration
            
            # Inner and outer points at constant width
            half_width = width / 2
            inner_pt = center_pt - normal * half_width
            outer_pt = center_pt + normal * half_width
            
            inner_curve.append(inner_pt)
            outer_curve.append(outer_pt)
        
        return inner_curve, outer_curve
    
    def get_sleeve_points(self, rib, num_points=50):
        """
        Get the sleeve outline points for visualization.
        Returns inner and outer polylines representing the sleeve pocket.
        """
        profile = rib.profile_2d
        chord = rib.chord
        
        start_x, end_x = self.get_profile_range(profile)
        start_idx = profile(start_x)
        end_idx = profile(end_x)
        
        profile_segment = list(profile[start_idx:end_idx])
        
        if len(profile_segment) < 2:
            return [], []
        
        offset_norm = self.offset / chord
        width_norm = self.width / chord
        
        inner_points = []
        outer_points = []
        
        for i, point in enumerate(profile_segment):
            normal = self._calculate_normal(profile_segment, i, self.surface)
            
            inner_pt = point + normal * offset_norm
            outer_pt = point + normal * (offset_norm + width_norm)
            
            inner_points.append(inner_pt * chord)
            outer_points.append(outer_pt * chord)
        
        return inner_points, outer_points
    
    def get_leading_edge_termination(self, rib):
        """
        Get the leading edge termination curve.
        Uses the actual sleeve direction for smooth connection.
        """
        inner_main, outer_main = self.get_sleeve_points(rib)
        
        if not inner_main or len(inner_main) < 2:
            return [], []
        
        inner_start = np.array(inner_main[0])
        outer_start = np.array(outer_main[0])
        
        # Calculate actual sleeve direction from first two points
        sleeve_dir = np.array(inner_main[0]) - np.array(inner_main[1])
        dir_len = np.linalg.norm(sleeve_dir)
        if dir_len > 1e-10:
            start_tangent = sleeve_dir / dir_len
        else:
            start_tangent = None
        
        return self._create_smooth_termination_with_width(
            inner_start, outer_start, self.le_angle, self.le_length,
            start_tangent_vec=start_tangent
        )
    
    def get_trailing_edge_termination(self, rib):
        """
        Get the trailing edge termination curve.
        Uses the actual sleeve direction for smooth connection.
        """
        inner_main, outer_main = self.get_sleeve_points(rib)
        
        if not inner_main or len(inner_main) < 2:
            return [], []
        
        inner_start = np.array(inner_main[-1])
        outer_start = np.array(outer_main[-1])
        
        # Calculate actual sleeve direction from last two points
        sleeve_dir = np.array(inner_main[-1]) - np.array(inner_main[-2])
        dir_len = np.linalg.norm(sleeve_dir)
        if dir_len > 1e-10:
            start_tangent = sleeve_dir / dir_len
        else:
            start_tangent = None
        
        return self._create_smooth_termination_with_width(
            inner_start, outer_start, self.te_angle, self.te_length,
            start_tangent_vec=start_tangent
        )
    
    def get_full_sleeve_points(self, rib):
        """
        Get the complete sleeve with leading and trailing edge terminations.
        """
        inner_main, outer_main = self.get_sleeve_points(rib)
        inner_le, outer_le = self.get_leading_edge_termination(rib)
        inner_te, outer_te = self.get_trailing_edge_termination(rib)
        
        # Combine: LE termination (reversed) + main sleeve + TE termination
        # Reverse LE so it connects properly (curves outward from main sleeve)
        # Slice to avoid duplicate points at junctions
        if inner_le:
            inner_start = list(reversed(inner_le))[:-1] if len(inner_le) > 0 else []
        else:
            inner_start = []
            
        if outer_le:
            outer_start = list(reversed(outer_le))[:-1] if len(outer_le) > 0 else []
        else:
            outer_start = []
            
        inner_end = inner_te[1:] if len(inner_te) > 1 else []
        outer_end = outer_te[1:] if len(outer_te) > 1 else []
        
        inner_full = inner_start + inner_main + inner_end
        outer_full = outer_start + outer_main + outer_end
        
        return inner_full, outer_full
    
    def get_flattened(self, rib, num_points=50):
        """
        Get the flattened 2D representation of the sleeve.
        Returns a closed polygon representing the sleeve pocket.
        """
        inner_points, outer_points = self.get_full_sleeve_points(rib)
        
        if not inner_points or not outer_points:
            return PolyLine2D([])
        
        polygon_points = []
        polygon_points.extend(inner_points)
        
        if len(inner_points) > 0 and len(outer_points) > 0:
            polygon_points.append(outer_points[-1])
        
        polygon_points.extend(reversed(outer_points))
        
        if len(inner_points) > 0:
            polygon_points.append(inner_points[0])
        
        return PolyLine2D(polygon_points)
    
    def get_3d(self, rib, num_points=50):
        """Get 3D representation of the sleeve."""
        flat = self.get_flattened(rib, num_points)
        return [rib.align([p[0], p[1], 0], scale=False) for p in flat.data]


class AttachmentReinforcement(object):
    """
    Reinforcement at attachment points with half-moon shape and optional rod sleeve.
    
    The half-moon has:
    - Outer edge following the intrados profile curve
    - Inner edge: circular arc centered on attachment point
    - Rod sleeve INSIDE the half-moon arc with end offset
    
    Attributes:
        position: Position on profile (chord %, e.g. 0.3 = 30%)
        surface_offset: Distance from profile surface to outer edge (m)
        halfmoon_radius: Radius of the circular arc (m)
        rod_enabled: Whether the rod sleeve is enabled
        rod_offset: Gap between half-moon arc and rod sleeve outer edge (m)
        rod_width: Thickness of the rod sleeve (m)
        rod_end_offset: Angular offset at ends so rod doesn't touch edges (degrees)
    """
    
    def __init__(
        self,
        position=0.0,
        surface_offset=0.003,
        halfmoon_radius=0.03,
        rod_enabled=True,
        rod_offset=0.005,
        rod_width=0.005,
        rod_end_offset=10.0,
        name="",
        material_code=None,
    ):
        self.position = position
        self.surface_offset = surface_offset
        self.halfmoon_radius = halfmoon_radius
        self.rod_enabled = rod_enabled
        self.rod_offset = rod_offset
        self.rod_width = rod_width
        self.rod_end_offset = rod_end_offset
        self.name = name
        self.material_code = material_code or ""
    
    def __json__(self):
        return {
            "position": self.position,
            "surface_offset": self.surface_offset,
            "halfmoon_radius": self.halfmoon_radius,
            "rod_enabled": self.rod_enabled,
            "rod_offset": self.rod_offset,
            "rod_width": self.rod_width,
            "rod_end_offset": self.rod_end_offset,
            "name": self.name,
            "material_code": self.material_code,
        }
    
    def _get_profile_section(self, rib, num_points=30):
        """Get a section of the profile around the attachment point."""
        profile = rib.profile_2d
        chord = rib.chord
        
        # Calculate position range based on radius (width = 2 * radius approximately)
        half_width_normalized = self.halfmoon_radius / chord
        start_pos = self.position - half_width_normalized
        end_pos = self.position + half_width_normalized
        
        # Get indices
        start_idx = profile(start_pos)
        end_idx = profile(end_pos)
        
        # Sample points along profile
        if start_idx > end_idx:
            start_idx, end_idx = end_idx, start_idx
        
        indices = np.linspace(start_idx, end_idx, num_points)
        
        points = []
        normals = []
        profile_normvectors = PolyLine2D(profile.normvectors)
        
        for idx in indices:
            # Get point on profile
            pt = profile[idx] * chord
            points.append(np.array(pt))
            
            # Get normal at this point
            int_idx = int(min(idx, len(profile_normvectors.data) - 1))
            norm = np.array(profile_normvectors.data[int_idx])
            norm_len = np.linalg.norm(norm)
            if norm_len > 1e-10:
                norm = norm / norm_len
            normals.append(norm)
        
        return points, normals
    
    def get_halfmoon_points(self, rib, num_points=30):
        """
        Get the half-moon (crescent) fabric reinforcement outline.
        
        - Outer edge: follows profile curve (with surface_offset)
        - Inner edge: circular ARC centered on attachment point
        """
        points, normals = self._get_profile_section(rib, num_points)
        
        if not points:
            return []
        
        # Get attachment point (center of the circular arc)
        profile = rib.profile_2d
        center_idx = profile(self.position)
        arc_center = np.array(profile[center_idx]) * rib.chord
        
        # Outer edge: follows profile with surface offset
        outer_points = []
        for pt, norm in zip(points, normals):
            outer_pt = pt - norm * self.surface_offset
            outer_points.append(outer_pt)
        
        # Calculate angular range from arc_center to outer edge endpoints
        start_vec = outer_points[0] - arc_center
        end_vec = outer_points[-1] - arc_center
        
        start_angle = np.arctan2(start_vec[1], start_vec[0])
        end_angle = np.arctan2(end_vec[1], end_vec[0])
        
        # Ensure we go the right way (shorter arc)
        angle_diff = end_angle - start_angle
        if angle_diff > np.pi:
            angle_diff -= 2 * np.pi
        elif angle_diff < -np.pi:
            angle_diff += 2 * np.pi
        
        # Inner edge: circular arc centered at attachment point, radius = halfmoon_radius
        inner_points = []
        for i in range(num_points):
            t = i / (num_points - 1)
            angle = start_angle + t * angle_diff
            
            inner_pt = arc_center + np.array([
                self.halfmoon_radius * np.cos(angle),
                self.halfmoon_radius * np.sin(angle)
            ])
            inner_points.append(inner_pt)
        
        # Combine: outer edge + reversed inner edge + close
        halfmoon = outer_points + list(reversed(inner_points)) + [outer_points[0]]
        
        return halfmoon
    
    def get_rod_sleeve_points(self, rib, num_points=30):
        """
        Get the rod sleeve that sits INSIDE the half-moon arc.
        Uses relative offsets from the half-moon arc and end offset to avoid touching edges.
        """
        if not self.rod_enabled:
            return [], []
        
        points, normals = self._get_profile_section(rib, num_points)
        
        if not points:
            return [], []
        
        # Get attachment point (center of arcs)
        profile = rib.profile_2d
        center_idx = profile(self.position)
        arc_center = np.array(profile[center_idx]) * rib.chord
        
        # Calculate angular range (same as half-moon)
        outer_points = []
        for pt, norm in zip(points, normals):
            outer_pt = pt - norm * self.surface_offset
            outer_points.append(outer_pt)
        
        start_vec = outer_points[0] - arc_center
        end_vec = outer_points[-1] - arc_center
        
        start_angle = np.arctan2(start_vec[1], start_vec[0])
        end_angle = np.arctan2(end_vec[1], end_vec[0])
        
        angle_diff = end_angle - start_angle
        if angle_diff > np.pi:
            angle_diff -= 2 * np.pi
        elif angle_diff < -np.pi:
            angle_diff += 2 * np.pi
        
        # Apply end offset (convert degrees to radians)
        end_offset_rad = np.deg2rad(self.rod_end_offset)
        rod_start_angle = start_angle + end_offset_rad * np.sign(angle_diff)
        rod_angle_diff = angle_diff - 2 * end_offset_rad * np.sign(angle_diff)
        
        # Rod sleeve: INSIDE the half-moon arc (closer to center)
        rod_outer_radius = self.halfmoon_radius - self.rod_offset
        rod_inner_radius = rod_outer_radius - self.rod_width
        
        # Ensure positive radii
        rod_outer_radius = max(0.001, rod_outer_radius)
        rod_inner_radius = max(0.001, rod_inner_radius)
        
        inner_curve = []
        outer_curve = []
        
        for i in range(num_points):
            t = i / (num_points - 1)
            angle = rod_start_angle + t * rod_angle_diff
            
            # Inner edge of rod sleeve (closer to center)
            inner_pt = arc_center + np.array([
                rod_inner_radius * np.cos(angle),
                rod_inner_radius * np.sin(angle)
            ])
            inner_curve.append(inner_pt)
            
            # Outer edge of rod sleeve (closer to half-moon arc)
            outer_pt = arc_center + np.array([
                rod_outer_radius * np.cos(angle),
                rod_outer_radius * np.sin(angle)
            ])
            outer_curve.append(outer_pt)
        
        return inner_curve, outer_curve
    
    def get_flattened(self, rib, num_points=30):
        """Get the flattened 2D representation."""
        halfmoon_points = self.get_halfmoon_points(rib, num_points)
        inner_rod, outer_rod = self.get_rod_sleeve_points(rib, num_points)
        
        # Create closed polygon for rod sleeve
        rod_points = []
        if inner_rod and outer_rod:
            rod_points = outer_rod + list(reversed(inner_rod)) + [outer_rod[0]]
        
        return {
            'halfmoon': PolyLine2D(halfmoon_points),
            'rod_sleeve': PolyLine2D(rod_points),
        }
    
    def get_3d(self, rib, num_points=30):
        """Get 3D representation."""
        flat = self.get_flattened(rib, num_points)
        return {
            'halfmoon': [rib.align([p[0], p[1], 0], scale=False) for p in flat['halfmoon'].data],
            'rod_sleeve': [rib.align([p[0], p[1], 0], scale=False) for p in flat['rod_sleeve'].data],
        }

