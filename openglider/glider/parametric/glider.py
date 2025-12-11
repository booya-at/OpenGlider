from __future__ import division

import math
import numpy as np
import copy

from openglider.glider.parametric.shape import ParametricShape
from openglider.airfoil import Profile2D
from openglider.glider.glider import Glider
from openglider.glider.cell import Panel, DiagonalRib, TensionStrap, TensionLine, Cell
from openglider.glider.cell.elements import PanelRigidFoil
from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.export_ods import export_ods_2d
from openglider.glider.parametric.import_ods import import_ods_2d
from openglider.glider.parametric.lines import LineSet2D, UpperNode2D
from openglider.glider.rib import RibHole, RigidFoil, Rib, MiniRib
from openglider.glider.parametric.fitglider import fit_glider_3d
from openglider.utils.distribution import Distribution
from openglider.utils.table import Table
from openglider.utils import ZipCmp
from openglider.utils.geometry import is_inside_triangle


class ParametricGlider(object):
    """
    A parametric (2D) Glider object used for gui input
    """

    num_arc_positions = 60
    num_shape = 30
    num_interpolate_ribs = 40
    num_cell_dist = 30
    num_depth_integral = 100
    num_interpolate = 30
    num_profile = None

    def __init__(
        self,
        shape,
        arc,
        aoa,
        profiles,
        profile_merge_curve,
        balloonings,
        ballooning_merge_curve,
        lineset,
        speed,
        glide,
        zrot,
        elements=None,
        **kwargs
    ):
        self.zrot = zrot or aoa
        self.shape: ParametricShape = shape
        self.arc = arc
        self.aoa = aoa
        self.profiles = profiles or []
        self.profile_merge_curve = profile_merge_curve
        self.balloonings = balloonings or []
        self.ballooning_merge_curve = ballooning_merge_curve
        self.lineset = lineset or LineSet2D([])
        self.speed = speed
        self.glide = glide
        self.elements = elements or {}

        # Hole properties
        self.holes = kwargs.get('holes', True)
        self.hole_shape_ns = kwargs.get('hole_shape_ns', 0)  # Default to Ellipse
        self.num_holes_ns = kwargs.get('num_holes_ns', 30)
        self.hole_width_ns = kwargs.get('hole_width_ns', 0.003)
        self.hole_height_ns = kwargs.get('hole_height_ns', 0.8)
        self.vertical_shift_ns = kwargs.get('vertical_shift_ns', 0.0)
        self.min_hole_pos_ns = kwargs.get('min_hole_pos_ns', 0.2)
        self.max_hole_pos_ns = kwargs.get('max_hole_pos_ns', 0.8)
        self.hole_height_mode_ns = kwargs.get('hole_height_mode_ns', 0)  # 0: Percent, 1: Margin
        self.hole_margin_ns = kwargs.get('hole_margin_ns', 0.02)    # 20mm
        self.hole_corner_radius_ns = kwargs.get('hole_corner_radius_ns', 0.25)  # Ratio of min dimension (0.25 = 25%)

        self.hole_shape_s = kwargs.get('hole_shape_s', 0)  # Default to Ellipse
        self.num_holes_s = kwargs.get('num_holes_s', 30)
        self.hole_width_s = kwargs.get('hole_width_s', 0.003)
        self.hole_height_s = kwargs.get('hole_height_s', 0.8)
        self.vertical_shift_s = kwargs.get('vertical_shift_s', 0.0)
        self.min_hole_pos_s = kwargs.get('min_hole_pos_s', 0.2)
        self.max_hole_pos_s = kwargs.get('max_hole_pos_s', 0.8)
        self.hole_height_mode_s = kwargs.get('hole_height_mode_s', 0)   # 0: Percent, 1: Margin
        self.hole_margin_s = kwargs.get('hole_margin_s', 0.02)     # 20mm
        self.hole_corner_radius_s = kwargs.get('hole_corner_radius_s', 0.25)  # Ratio of min dimension (0.25 = 25%)

        # No-hole zone parameters for suspended ribs
        self.hole_free_angle_s = kwargs.get('hole_free_angle_s', 30.0)  # degrees
        self.susp_hole_num_s = kwargs.get('susp_hole_num_s', 3)  # Number of truss holes
        self.susp_hole_margin_s = kwargs.get('susp_hole_margin_s', 0.01)  # Margin in meters
        self.susp_hole_radius_top_s = kwargs.get('susp_hole_radius_top_s', 0.005)  # Top corner radius
        self.susp_hole_radius_bottom_s = kwargs.get('susp_hole_radius_bottom_s', 0.005)  # Bottom corner radius

        # Minirib hole parameters
        self.minirib_holes = kwargs.get('minirib_holes', False)  # Enable holes in miniribs (disabled by default)
        self.minirib_num_holes = kwargs.get('minirib_num_holes', 1)  # Number of holes per minirib (when enabled)
        self.minirib_hole_width = kwargs.get('minirib_hole_width', 0.5)  # Width ratio (0-1 of minirib width)
        self.minirib_hole_height = kwargs.get('minirib_hole_height', 0.7)  # Height ratio (0-1 of minirib height)
        self.minirib_hole_shape = kwargs.get('minirib_hole_shape', 0)  # 0=Ellipse, 1=Rounded Rectangle
        self.minirib_hole_corner_radius = kwargs.get('minirib_hole_corner_radius', 0.25)  # Corner radius ratio
        self.minirib_hole_max_pos = kwargs.get('minirib_hole_max_pos', 0.9)  # Max position (0-1, limits holes to avoid thin tip)

        # Airfoil Structure - Extrados Sleeve (suspended)
        self.extrados_sleeve_enabled_s = kwargs.get('extrados_sleeve_enabled_s', False)
        self.extrados_sleeve_width_s = kwargs.get('extrados_sleeve_width_s', 0.015)
        self.extrados_sleeve_offset_s = kwargs.get('extrados_sleeve_offset_s', 0.003)
        self.extrados_sleeve_start_s = kwargs.get('extrados_sleeve_start_s', 0.0)
        self.extrados_sleeve_end_s = kwargs.get('extrados_sleeve_end_s', 0.9)
        self.extrados_sleeve_le_angle_s = kwargs.get('extrados_sleeve_le_angle_s', 80.0)
        self.extrados_sleeve_le_length_s = kwargs.get('extrados_sleeve_le_length_s', 0.03)
        self.extrados_sleeve_te_angle_s = kwargs.get('extrados_sleeve_te_angle_s', 80.0)
        self.extrados_sleeve_te_length_s = kwargs.get('extrados_sleeve_te_length_s', 0.03)
        
        # Airfoil Structure - Intrados Sleeve (suspended)
        self.intrados_sleeve_enabled_s = kwargs.get('intrados_sleeve_enabled_s', False)
        self.intrados_sleeve_width_s = kwargs.get('intrados_sleeve_width_s', 0.015)
        self.intrados_sleeve_offset_s = kwargs.get('intrados_sleeve_offset_s', 0.003)
        self.intrados_sleeve_start_s = kwargs.get('intrados_sleeve_start_s', 0.0)
        self.intrados_sleeve_end_s = kwargs.get('intrados_sleeve_end_s', 0.9)
        self.intrados_sleeve_le_angle_s = kwargs.get('intrados_sleeve_le_angle_s', 100.0)
        self.intrados_sleeve_le_length_s = kwargs.get('intrados_sleeve_le_length_s', 0.03)
        self.intrados_sleeve_te_angle_s = kwargs.get('intrados_sleeve_te_angle_s', 100.0)
        self.intrados_sleeve_te_length_s = kwargs.get('intrados_sleeve_te_length_s', 0.03)
        
        # Airfoil Structure - Extrados Sleeve (non-suspended)
        self.extrados_sleeve_enabled_ns = kwargs.get('extrados_sleeve_enabled_ns', False)
        self.extrados_sleeve_width_ns = kwargs.get('extrados_sleeve_width_ns', 0.015)
        self.extrados_sleeve_offset_ns = kwargs.get('extrados_sleeve_offset_ns', 0.003)
        self.extrados_sleeve_start_ns = kwargs.get('extrados_sleeve_start_ns', 0.0)
        self.extrados_sleeve_end_ns = kwargs.get('extrados_sleeve_end_ns', 0.9)
        self.extrados_sleeve_le_angle_ns = kwargs.get('extrados_sleeve_le_angle_ns', 80.0)
        self.extrados_sleeve_le_length_ns = kwargs.get('extrados_sleeve_le_length_ns', 0.03)
        self.extrados_sleeve_te_angle_ns = kwargs.get('extrados_sleeve_te_angle_ns', 80.0)
        self.extrados_sleeve_te_length_ns = kwargs.get('extrados_sleeve_te_length_ns', 0.03)
        
        # Airfoil Structure - Intrados Sleeve (non-suspended)
        self.intrados_sleeve_enabled_ns = kwargs.get('intrados_sleeve_enabled_ns', False)
        self.intrados_sleeve_width_ns = kwargs.get('intrados_sleeve_width_ns', 0.015)
        self.intrados_sleeve_offset_ns = kwargs.get('intrados_sleeve_offset_ns', 0.003)
        self.intrados_sleeve_start_ns = kwargs.get('intrados_sleeve_start_ns', 0.0)
        self.intrados_sleeve_end_ns = kwargs.get('intrados_sleeve_end_ns', 0.9)
        self.intrados_sleeve_le_angle_ns = kwargs.get('intrados_sleeve_le_angle_ns', 100.0)
        self.intrados_sleeve_le_length_ns = kwargs.get('intrados_sleeve_le_length_ns', 0.03)
        self.intrados_sleeve_te_angle_ns = kwargs.get('intrados_sleeve_te_angle_ns', 100.0)
        self.intrados_sleeve_te_length_ns = kwargs.get('intrados_sleeve_te_length_ns', 0.03)
        
        # Airfoil Structure - Reinforcements (suspended only)
        self.reinforcement_enabled_s = kwargs.get('reinforcement_enabled_s', True)  # Enabled by default
        self.reinforcement_apply_all_s = kwargs.get('reinforcement_apply_all_s', False)  # Individual config by default
        self.reinforcement_master_s = kwargs.get('reinforcement_master_s', {
            'enabled': True,
            'surface_offset': 0.0005,  # 0.5mm
            'halfmoon_radius': 0.1,    # 100mm
            'rod_enabled': True,
            'rod_offset': 0.008,       # 8mm
            'rod_width': 0.009,        # 9mm
            'rod_end_offset': 1.0,     # 1°
        })
        self.reinforcement_configs_s = kwargs.get('reinforcement_configs_s', [])

        # Multi-rod sleeves (NEW FORMAT - list of configs)
        # Suspended ribs
        self.extrados_sleeves_enabled_s = kwargs.get('extrados_sleeves_enabled_s', True)
        self.extrados_sleeves_s = kwargs.get('extrados_sleeves_s', [])
        self.intrados_sleeves_enabled_s = kwargs.get('intrados_sleeves_enabled_s', True)
        self.intrados_sleeves_s = kwargs.get('intrados_sleeves_s', [])
        # Non-suspended ribs
        self.extrados_sleeves_enabled_ns = kwargs.get('extrados_sleeves_enabled_ns', True)
        self.extrados_sleeves_ns = kwargs.get('extrados_sleeves_ns', [])
        self.intrados_sleeves_enabled_ns = kwargs.get('intrados_sleeves_enabled_ns', True)
        self.intrados_sleeves_ns = kwargs.get('intrados_sleeves_ns', [])

    def get_sleeve_exclusion_zones(self, rib, rib_idx, is_suspended):
        """
        Get chord ranges that should be excluded from hole placement due to rod sleeves.
        Returns list of (start_chord, end_chord) tuples.
        """
        suffix = '_s' if is_suspended else '_ns'
        exclusion_zones = []
        
        # Check extrados sleeves
        if getattr(self, f'extrados_sleeves_enabled{suffix}', True):
            for config in getattr(self, f'extrados_sleeves{suffix}', []):
                excluded_ribs = config.get('excluded_ribs', [])
                if rib_idx not in excluded_ribs:
                    start = config.get('start_chord', 0.0)
                    end = config.get('end_chord', 0.7)
                    if start < end:
                        exclusion_zones.append((start, end))
        
        # Check intrados sleeves
        if getattr(self, f'intrados_sleeves_enabled{suffix}', True):
            for config in getattr(self, f'intrados_sleeves{suffix}', []):
                excluded_ribs = config.get('excluded_ribs', [])
                if rib_idx not in excluded_ribs:
                    start = config.get('start_chord', 0.06)
                    end = config.get('end_chord', 0.5)
                    if start < end:
                        exclusion_zones.append((start, end))
        
        return exclusion_zones
    
    def get_reinforcement_exclusion_zones(self, rib, glider):
        """
        Get chord ranges that should be excluded from hole placement due to attachment reinforcements.
        Returns list of (start_chord, end_chord) tuples.
        """
        exclusion_zones = []
        
        if not getattr(self, 'reinforcement_enabled_s', False):
            return exclusion_zones
        
        apply_all = getattr(self, 'reinforcement_apply_all_s', False)
        master_config = getattr(self, 'reinforcement_master_s', {})
        configs = getattr(self, 'reinforcement_configs_s', [])
        
        attachment_points = glider.get_rib_attachment_points(rib)
        valid_aps = [ap for ap in attachment_points if ap.rib_pos <= 0.90]
        valid_aps.sort(key=lambda x: x.rib_pos)
        
        for i, ap in enumerate(valid_aps):
            if apply_all:
                config = master_config
            else:
                config = configs[i] if i < len(configs) else master_config
            
            if config.get('enabled', True):
                radius_normalized = config.get('halfmoon_radius', 0.03) / rib.chord
                start = max(0.0, ap.rib_pos - radius_normalized)
                end = min(1.0, ap.rib_pos + radius_normalized)
                exclusion_zones.append((start, end))
        
        return exclusion_zones
    
    def subtract_exclusion_zones(self, allowed_ranges, exclusion_zones):
        """
        Remove exclusion zones from allowed ranges.
        Both inputs are lists of (start, end) tuples.
        Returns a new list of allowed (start, end) tuples.
        """
        if not exclusion_zones:
            return allowed_ranges
        
        # Sort exclusion zones by start position
        exclusions = sorted(exclusion_zones, key=lambda x: x[0])
        
        result = []
        for start, end in allowed_ranges:
            current_start = start
            for ex_start, ex_end in exclusions:
                if ex_end <= current_start or ex_start >= end:
                    # No overlap with this exclusion
                    continue
                if ex_start > current_start:
                    # Add the gap before this exclusion
                    result.append((current_start, min(ex_start, end)))
                current_start = max(current_start, ex_end)
                if current_start >= end:
                    break
            if current_start < end:
                result.append((current_start, end))
        
        return result

    def apply_holes(self, glider):
        if not self.holes:
            return

        suspended_ribs = {att.rib for att in glider.lineset.attachment_points if hasattr(att, 'rib')}

        NO_HOLE_ZONE_BASE_CHORD_FRACTION = 0.05

        for rib in glider.ribs:
            is_suspended = rib in suspended_ribs

            if is_suspended:
                shape_idx, num_holes, w_factor, h_factor, v_shift_factor, start_pos, end_pos, hole_height_mode, hole_margin, corner_radius = (
                    getattr(self, 'hole_shape_s', 0), self.num_holes_s, self.hole_width_s,
                    self.hole_height_s, self.vertical_shift_s, self.min_hole_pos_s, self.max_hole_pos_s,
                    self.hole_height_mode_s, self.hole_margin_s, getattr(self, 'hole_corner_radius_s', 0.005)
                )
                no_hole_zones = []
                attachment_points = glider.get_rib_attachment_points(rib)
                for ap in attachment_points:
                    v1 = rib.profile_2d.align([ap.rib_pos, -1.0]) # Apex on intrados

                    angle_rad = np.deg2rad(self.hole_free_angle_s)

                    # Define two lines starting from v1, going up at +/- angle
                    # We need a reference direction. Use the local vertical.
                    upper_point = rib.profile_2d.align([ap.rib_pos, 1.0])
                    local_vertical = upper_point - v1
                    if np.linalg.norm(local_vertical) < 1e-9: continue # Skip if profile is flat
                    local_vertical /= np.linalg.norm(local_vertical)

                    # Rotate the local vertical to get the triangle leg directions
                    angle_offset = np.arctan2(local_vertical[1], local_vertical[0])

                    dir2 = np.array([np.cos(angle_offset - angle_rad), np.sin(angle_offset - angle_rad)])
                    dir3 = np.array([np.cos(angle_offset + angle_rad), np.sin(angle_offset + angle_rad)])

                    # Find intersection of these lines with the upper surface (extrados)
                    extrados_poly = rib.profile_2d.get_extrados_poly()

                    far_factor = rib.chord * 100
                    v2 = extrados_poly.line_intersection(v1, v1 + dir2 * far_factor)
                    v3 = extrados_poly.line_intersection(v1, v1 + dir3 * far_factor)

                    if v2 is not None and v3 is not None:
                        no_hole_zones.append((v1, v2, v3))
                        
                        # Generate truss holes inside this zone
                        if self.susp_hole_num_s > 0:
                            truss_holes = self.generate_truss_holes(
                                rib, v1, v2, v3, 
                                self.susp_hole_num_s, 
                                self.susp_hole_margin_s, 
                                self.susp_hole_radius_top_s,
                                self.susp_hole_radius_bottom_s
                            )
                            for hole_poly in truss_holes:
                                rib.holes.append(RibHole(pos=0.0, custom_points=hole_poly))

            else:
                shape_idx, num_holes, w_factor, h_factor, v_shift_factor, start_pos, end_pos, hole_height_mode, hole_margin, corner_radius = (
                    getattr(self, 'hole_shape_ns', 0), self.num_holes_ns, self.hole_width_ns,
                    self.hole_height_ns, self.vertical_shift_ns, self.min_hole_pos_ns, self.max_hole_pos_ns,
                    self.hole_height_mode_ns, self.hole_margin_ns, getattr(self, 'hole_corner_radius_ns', 0.005)
                )
                no_hole_zones = []

            hole_shape = 'ellipse' if shape_idx == 0 else 'rounded_rectangle'

            if num_holes == 0:
                continue

            allowed_ranges = [(start_pos, end_pos)]

            total_allowable_length = sum(end - start for start, end in allowed_ranges)
            if total_allowable_length <= 1e-6:
                continue

            holes_to_distribute = num_holes
            for i, (start, end) in enumerate(allowed_ranges):
                range_length = end - start
                if range_length <= 0: continue

                is_last_range = (i == len(allowed_ranges) - 1)
                if is_last_range:
                    num_holes_in_range = holes_to_distribute
                else:
                    num_holes_in_range = int(round(num_holes * (range_length / total_allowable_length)))

                if num_holes_in_range <= 0:
                    continue

                holes_to_distribute -= num_holes_in_range

                if num_holes_in_range == 1:
                    potential_positions = [start + range_length / 2] # Center the single hole
                else:
                    potential_positions = np.linspace(start, end, num_holes_in_range)

                for pos_x in potential_positions:
                    upper = rib.profile_2d.profilepoint(-pos_x)
                    lower = rib.profile_2d.profilepoint(pos_x)
                    local_thickness = upper[1] - lower[1]
                    if local_thickness < 1e-6:
                        continue

                    if is_suspended:
                        hole_center_x = (upper[0] + lower[0]) / 2.0
                        min_y_ceiling = upper[1]

                        for v1, v2, v3 in no_hole_zones:
                            if min(v1[0], v2[0], v3[0]) <= hole_center_x <= max(v1[0], v2[0], v3[0]):
                                for p1, p2 in [(v1, v2), (v2, v3), (v3, v1)]:
                                    if p1[0] != p2[0] and ((p1[0] <= hole_center_x <= p2[0]) or (p2[0] <= hole_center_x <= p1[0])):
                                        y_intersect = p1[1] + (p2[1] - p1[1]) * (hole_center_x - p1[0]) / (p2[0] - p1[0])
                                        if y_intersect < min_y_ceiling: # Constrain ceiling from above
                                             min_y_ceiling = min(min_y_ceiling, y_intersect)

                        available_height = min_y_ceiling - lower[1]
                        hole_center_y = lower[1] + available_height / 2
                        new_lower_bound = np.array([hole_center_x, lower[1]]) # Base for vertical shift calculation logic
                        eff_upper_bound = np.array([hole_center_x, min_y_ceiling])
                    else:
                        available_height = upper[1] - lower[1]
                        new_lower_bound = lower
                        eff_upper_bound = upper

                    if available_height < 1e-4:
                        continue

                    # vertical shift is relative to LOCAL THICKNESS if we wanted to maintain consistent offset logic,
                    # but here we want to center in the AVAILABLE space usually.
                    # The original code used new_lower_bound + (available_height)/2 * (1+shift).
                    # Let's align with that.
                    
                    hole_center = np.array([hole_center_x if is_suspended else (upper[0]+lower[0])/2, lower[1] + available_height / 2])
                    
                    if not is_suspended: # Respect original shift logic for non-suspended
                         hole_center = lower + (upper - lower) / 2 * (1 + v_shift_factor)

                    # For suspended, we might want to respect vertical shift within the NEW available height?
                    if is_suspended:
                         hole_center[1] += available_height / 2 * v_shift_factor
                    
                    # Calculate final_vertical_shift relative to full local thickness
                    full_thickness = upper[1] - lower[1]
                    if full_thickness < 1e-6: continue
                    
                    original_center_y = (upper[1] + lower[1]) / 2.0
                    final_vertical_shift = (hole_center[1] - original_center_y) / full_thickness

                    width_param = (w_factor * rib.chord) / available_height if available_height > 1e-6 else 0
                    
                    # Calculate height parameter based on mode
                    # RibHole interprets size[1] as a factor of available_height (or local_thickness)
                    if hole_height_mode == 1: # Margin mode
                        target_height = available_height - 2 * hole_margin
                        if target_height <= 0:
                            continue
                        height_param = target_height / available_height
                    else: # Percent mode
                        height_param = h_factor

                    rib.holes.append(
                        RibHole(
                            pos_x,
                            size=np.array([width_param, height_param]),
                            vertical_shift=final_vertical_shift,
                            rotation=0.0,
                            shape=hole_shape,
                            available_height=available_height,
                            corner_radius=corner_radius
                        )
                    )

    def apply_reinforcements(self, glider):
        """Apply reinforcement configurations to ribs for 2D export."""
        from openglider.glider.rib.elements import AttachmentReinforcement
        
        if not getattr(self, 'reinforcement_enabled_s', False):
            # Clear reinforcements from all ribs
            for rib in glider.ribs:
                rib.reinforcements = []
            return
        
        apply_all = getattr(self, 'reinforcement_apply_all_s', False)
        master_config = getattr(self, 'reinforcement_master_s', {})
        configs = getattr(self, 'reinforcement_configs_s', [])
        
        # Identify suspended ribs
        suspended_ribs = {att.rib for att in glider.lineset.attachment_points if hasattr(att, 'rib')}
        
        for rib_idx, rib in enumerate(glider.ribs):
            if rib in suspended_ribs:
                # Get attachment points for this rib
                attachment_points = glider.get_rib_attachment_points(rib)
                # Filter to valid attachment points (< 90% chord)
                valid_aps = [ap for ap in attachment_points if ap.rib_pos <= 0.90]
                valid_aps.sort(key=lambda x: x.rib_pos)
                
                reinforcements = []
                for i, ap in enumerate(valid_aps):
                    # Get config
                    if apply_all:
                        config = master_config
                    else:
                        config = configs[i] if i < len(configs) else master_config
                    
                    if config.get('enabled', True):
                        # Generate name: rib index + attachment point name
                        name = f"{rib_idx + 1}{ap.name}" if ap.name else f"{rib_idx + 1}_{i + 1}"
                        
                        reinforcement = AttachmentReinforcement(
                            position=ap.rib_pos,
                            surface_offset=config.get('surface_offset', 0.0005),  # 0.5mm
                            halfmoon_radius=config.get('halfmoon_radius', 0.1),   # 100mm
                            rod_enabled=config.get('rod_enabled', True),
                            rod_offset=config.get('rod_offset', 0.008),           # 8mm
                            rod_width=config.get('rod_width', 0.009),             # 9mm
                            rod_end_offset=config.get('rod_end_offset', 1.0),     # 1°
                            name=name,
                        )
                        reinforcements.append(reinforcement)

                
                rib.reinforcements = reinforcements
            else:
                # Non-suspended ribs don't get reinforcements
                rib.reinforcements = []

    def apply_rod_sleeves(self, glider):
        """Apply rod sleeve configurations to ribs for 2D export."""
        from openglider.glider.rib.elements import RodSleeve
        
        # Identify suspended ribs
        suspended_ribs = {att.rib for att in glider.lineset.attachment_points if hasattr(att, 'rib')}
        
        for rib_idx, rib in enumerate(glider.ribs):
            is_suspended = rib in suspended_ribs
            suffix = '_s' if is_suspended else '_ns'
            
            rod_sleeves = []
            
            # Get extrados sleeves
            extrados_enabled = getattr(self, f'extrados_sleeves_enabled{suffix}', True)
            extrados_configs = getattr(self, f'extrados_sleeves{suffix}', [])
            
            if extrados_enabled and extrados_configs:
                for i, config in enumerate(extrados_configs):
                    # Check if this rib is excluded for this config
                    excluded_ribs = config.get('excluded_ribs', [])
                    if rib_idx in excluded_ribs:
                        continue
                    
                    sleeve = RodSleeve(
                        surface='extrados',
                        width=config.get('width', 0.015),
                        offset=config.get('offset', 0.005),
                        start_chord=config.get('start_chord', 0.0),
                        end_chord=config.get('end_chord', 0.7),
                        le_angle=config.get('start_angle', 350.0),
                        te_angle=config.get('end_angle', 325.0),
                        le_length=config.get('start_length', 0.1),
                        te_length=config.get('end_length', 0.075),
                    )
                    rod_sleeves.append(sleeve)
            
            # Get intrados sleeves
            intrados_enabled = getattr(self, f'intrados_sleeves_enabled{suffix}', True)
            intrados_configs = getattr(self, f'intrados_sleeves{suffix}', [])
            
            if intrados_enabled and intrados_configs:
                for i, config in enumerate(intrados_configs):
                    # Check if this rib is excluded for this config
                    excluded_ribs = config.get('excluded_ribs', [])
                    if rib_idx in excluded_ribs:
                        continue
                    
                    sleeve = RodSleeve(
                        surface='intrados',
                        width=config.get('width', 0.015),
                        offset=config.get('offset', 0.005),
                        start_chord=config.get('start_chord', 0.06),
                        end_chord=config.get('end_chord', 0.5),
                        le_angle=config.get('start_angle', 100.0),
                        te_angle=config.get('end_angle', 20.0),
                        le_length=config.get('start_length', 0.1),
                        te_length=config.get('end_length', 0.09),
                    )
                    rod_sleeves.append(sleeve)
            
            rib.rod_sleeves = rod_sleeves

    def __json__(self):
        return {
            "shape": self.shape,
            "arc": self.arc,
            "aoa": self.aoa,
            "zrot": self.zrot,
            "profiles": self.profiles,
            "profile_merge_curve": self.profile_merge_curve,
            "balloonings": self.balloonings,
            "ballooning_merge_curve": self.ballooning_merge_curve,
            "lineset": self.lineset,
            "speed": self.speed,
            "glide": self.glide,
            "elements": self.elements,
            "hole_shape_ns": getattr(self, "hole_shape_ns", 0),
            "num_holes_ns": getattr(self, "num_holes_ns", 30),
            "hole_width_ns": getattr(self, "hole_width_ns", 0.003),
            "hole_height_ns": getattr(self, "hole_height_ns", 0.8),
            "vertical_shift_ns": getattr(self, "vertical_shift_ns", 0.0),
            "min_hole_pos_ns": getattr(self, "min_hole_pos_ns", 0.2),
            "max_hole_pos_ns": getattr(self, "max_hole_pos_ns", 0.8),
            "hole_height_mode_ns": getattr(self, "hole_height_mode_ns", 0),
            "hole_margin_ns": getattr(self, "hole_margin_ns", 0.02),
            "hole_corner_radius_ns": getattr(self, "hole_corner_radius_ns", 0.005),
            "hole_shape_s": getattr(self, "hole_shape_s", 0),
            "num_holes_s": getattr(self, "num_holes_s", 30),
            "hole_width_s": getattr(self, "hole_width_s", 0.003),
            "hole_height_s": getattr(self, "hole_height_s", 0.8),
            "vertical_shift_s": getattr(self, "vertical_shift_s", 0.0),
            "min_hole_pos_s": getattr(self, "min_hole_pos_s", 0.2),
            "max_hole_pos_s": getattr(self, "max_hole_pos_s", 0.8),
            "hole_height_mode_s": getattr(self, "hole_height_mode_s", 0),
            "hole_margin_s": getattr(self, "hole_margin_s", 0.02),
            "hole_corner_radius_s": getattr(self, "hole_corner_radius_s", 0.005),
            "hole_free_angle_s": getattr(self, "hole_free_angle_s", 30.0),
            "susp_hole_num_s": getattr(self, "susp_hole_num_s", 3),
            "susp_hole_margin_s": getattr(self, "susp_hole_margin_s", 0.01),
            "susp_hole_num_s": getattr(self, "susp_hole_num_s", 3),
            "susp_hole_margin_s": getattr(self, "susp_hole_margin_s", 0.01),
            "susp_hole_radius_top_s": getattr(self, "susp_hole_radius_top_s", 0.005),
            "susp_hole_radius_bottom_s": getattr(self, "susp_hole_radius_bottom_s", 0.005),
            # Minirib hole parameters
            "minirib_holes": getattr(self, "minirib_holes", False),
            "minirib_num_holes": getattr(self, "minirib_num_holes", 1),
            "minirib_hole_width": getattr(self, "minirib_hole_width", 0.5),
            "minirib_hole_height": getattr(self, "minirib_hole_height", 0.7),
            "minirib_hole_shape": getattr(self, "minirib_hole_shape", 0),
            "minirib_hole_corner_radius": getattr(self, "minirib_hole_corner_radius", 0.25),
            "minirib_hole_max_pos": getattr(self, "minirib_hole_max_pos", 0.9),
            # Airfoil Structure - Extrados Sleeve (suspended)
            "extrados_sleeve_enabled_s": getattr(self, "extrados_sleeve_enabled_s", False),
            "extrados_sleeve_width_s": getattr(self, "extrados_sleeve_width_s", 0.015),
            "extrados_sleeve_offset_s": getattr(self, "extrados_sleeve_offset_s", 0.003),
            "extrados_sleeve_start_s": getattr(self, "extrados_sleeve_start_s", 0.0),
            "extrados_sleeve_end_s": getattr(self, "extrados_sleeve_end_s", 0.9),
            "extrados_sleeve_le_angle_s": getattr(self, "extrados_sleeve_le_angle_s", 80.0),
            "extrados_sleeve_le_length_s": getattr(self, "extrados_sleeve_le_length_s", 0.03),
            "extrados_sleeve_te_angle_s": getattr(self, "extrados_sleeve_te_angle_s", 80.0),
            "extrados_sleeve_te_length_s": getattr(self, "extrados_sleeve_te_length_s", 0.03),
            # Airfoil Structure - Intrados Sleeve (suspended)
            "intrados_sleeve_enabled_s": getattr(self, "intrados_sleeve_enabled_s", False),
            "intrados_sleeve_width_s": getattr(self, "intrados_sleeve_width_s", 0.015),
            "intrados_sleeve_offset_s": getattr(self, "intrados_sleeve_offset_s", 0.003),
            "intrados_sleeve_start_s": getattr(self, "intrados_sleeve_start_s", 0.0),
            "intrados_sleeve_end_s": getattr(self, "intrados_sleeve_end_s", 0.9),
            "intrados_sleeve_le_angle_s": getattr(self, "intrados_sleeve_le_angle_s", 100.0),
            "intrados_sleeve_le_length_s": getattr(self, "intrados_sleeve_le_length_s", 0.03),
            "intrados_sleeve_te_angle_s": getattr(self, "intrados_sleeve_te_angle_s", 100.0),
            "intrados_sleeve_te_length_s": getattr(self, "intrados_sleeve_te_length_s", 0.03),
            # Airfoil Structure - Extrados Sleeve (non-suspended)
            "extrados_sleeve_enabled_ns": getattr(self, "extrados_sleeve_enabled_ns", False),
            "extrados_sleeve_width_ns": getattr(self, "extrados_sleeve_width_ns", 0.015),
            "extrados_sleeve_offset_ns": getattr(self, "extrados_sleeve_offset_ns", 0.003),
            "extrados_sleeve_start_ns": getattr(self, "extrados_sleeve_start_ns", 0.0),
            "extrados_sleeve_end_ns": getattr(self, "extrados_sleeve_end_ns", 0.9),
            "extrados_sleeve_le_angle_ns": getattr(self, "extrados_sleeve_le_angle_ns", 80.0),
            "extrados_sleeve_le_length_ns": getattr(self, "extrados_sleeve_le_length_ns", 0.03),
            "extrados_sleeve_te_angle_ns": getattr(self, "extrados_sleeve_te_angle_ns", 80.0),
            "extrados_sleeve_te_length_ns": getattr(self, "extrados_sleeve_te_length_ns", 0.03),
            # Airfoil Structure - Intrados Sleeve (non-suspended)
            "intrados_sleeve_enabled_ns": getattr(self, "intrados_sleeve_enabled_ns", False),
            "intrados_sleeve_width_ns": getattr(self, "intrados_sleeve_width_ns", 0.015),
            "intrados_sleeve_offset_ns": getattr(self, "intrados_sleeve_offset_ns", 0.003),
            "intrados_sleeve_start_ns": getattr(self, "intrados_sleeve_start_ns", 0.0),
            "intrados_sleeve_end_ns": getattr(self, "intrados_sleeve_end_ns", 0.9),
            "intrados_sleeve_le_angle_ns": getattr(self, "intrados_sleeve_le_angle_ns", 100.0),
            "intrados_sleeve_le_length_ns": getattr(self, "intrados_sleeve_le_length_ns", 0.03),
            "intrados_sleeve_te_angle_ns": getattr(self, "intrados_sleeve_te_angle_ns", 100.0),
            "intrados_sleeve_te_length_ns": getattr(self, "intrados_sleeve_te_length_ns", 0.03),
            # Airfoil Structure - Reinforcements (suspended only)
            "reinforcement_enabled_s": getattr(self, "reinforcement_enabled_s", True),
            "reinforcement_apply_all_s": getattr(self, "reinforcement_apply_all_s", False),
            "reinforcement_master_s": getattr(self, "reinforcement_master_s", {
                'enabled': True, 'surface_offset': 0.0005, 'halfmoon_radius': 0.1,
                'rod_enabled': True, 'rod_offset': 0.008, 'rod_width': 0.009, 'rod_end_offset': 1.0
            }),
            "reinforcement_configs_s": getattr(self, "reinforcement_configs_s", []),
            # Multi-rod sleeves (NEW FORMAT)
            "extrados_sleeves_enabled_s": getattr(self, "extrados_sleeves_enabled_s", True),
            "extrados_sleeves_s": getattr(self, "extrados_sleeves_s", []),
            "intrados_sleeves_enabled_s": getattr(self, "intrados_sleeves_enabled_s", True),
            "intrados_sleeves_s": getattr(self, "intrados_sleeves_s", []),
            "extrados_sleeves_enabled_ns": getattr(self, "extrados_sleeves_enabled_ns", True),
            "extrados_sleeves_ns": getattr(self, "extrados_sleeves_ns", []),
            "intrados_sleeves_enabled_ns": getattr(self, "intrados_sleeves_enabled_ns", True),
            "intrados_sleeves_ns": getattr(self, "intrados_sleeves_ns", []),
        }



    def generate_truss_holes(self, rib, v1, v2, v3, num_holes, margin, radius_top=0.0, radius_bottom=0.0):
        """
        Generate triangular holes inside the triangle defined by v1, v2, v3.
        v1 is the apex (top). v2, v3 are the base (bottom).
        """
        holes = []
        if num_holes < 1: return holes

        base_vec = v3 - v2
        
        # Points along the base v2-v3
        base_points = [v2 + base_vec * (i / float(num_holes)) for i in range(num_holes + 1)]
        
        for i in range(num_holes):
            p1, p2, p3 = v1, base_points[i], base_points[i+1]
            
            # Use separate radii for top and bottom vertices
            # v1 is the apex (top), v2 is top-left, v3 is top-right (bottom)
            # So p1 (v1) -> radius_top, p2 -> radius_top, p3 -> radius_bottom
            radii = [radius_top, radius_top, radius_bottom]
            
            poly = self.inset_polygon([p1, p2, p3], margin)
            if poly is not None and len(poly) >= 3:
                # Apply rounding
                poly = self.round_polygon_corners(poly, radii)
                
                # Validate polygon has enough points
                if len(poly) < 3:
                    continue
                    
                # Ensure closure
                if len(poly) > 0 and np.linalg.norm(np.array(poly[0]) - np.array(poly[-1])) > 1e-9:
                    poly.append(poly[0])
                
                # Validate polygon area is positive (not degenerate)
                area = abs(self._polygon_area(poly))
                if area < 1e-12:
                    continue  # Skip degenerate polygons
                         
                holes.append(poly)
                
        return holes
        
    def round_polygon_corners(self, points, radii):
        """
        Round the corners of a polygon with given radii.
        points: list of numpy arrays (vertices)
        radii: float or list of floats (per vertex)
        """
        # Handle scalar radius
        if isinstance(radii, (int, float)):
             if radii <= 1e-6: return points
             radii = [float(radii)] * len(points)
        
        # Ensure radii list matches points length if list provided
        # If points list is smaller than radii (e.g. polygon collapsed?), handle gracefully
        # Or if points list is closed? we usually process unique vertices here.
        # Calling logic passes 3 points.
        
        n = len(points)
        if len(radii) < n:
            radii = (list(radii) + [0.0] * n)[:n]
            
        new_points = []
        
        for i in range(n):
            radius = radii[i]
            
            if radius <= 1e-6:
                new_points.append(points[i])
                continue
            
            p_prev = points[(i - 1) % n]
            p_curr = points[i]
            p_next = points[(i + 1) % n]
            
            # ... (rest of rounding logic using 'radius') ...
            
            # Vectors from current point
            v_prev = p_prev - p_curr
            v_next = p_next - p_curr
            
            len_prev = np.linalg.norm(v_prev)
            len_next = np.linalg.norm(v_next)
            
            if len_prev < 1e-9 or len_next < 1e-9:
                new_points.append(p_curr)
                continue
                
            v_prev /= len_prev
            v_next /= len_next
            
            # Angle between vectors
            angle = np.arccos(np.clip(np.dot(v_prev, v_next), -1.0, 1.0))
            
            # Distance from corner to tangent points
            if angle < 1e-3 or abs(angle - np.pi) < 1e-3:
                 new_points.append(p_curr)
                 continue
                 
            dist = radius / np.tan(angle / 2.0)
            
            # Limit distance to half the edge length to prevent overlap
            limit = min(len_prev, len_next) / 2.0
            actual_radius = radius
            if dist > limit:
                dist = limit
                # Re-calculate radius if we had to clamp dist
                actual_radius = dist * np.tan(angle / 2.0)
                
            t_prev = p_curr + v_prev * dist
            t_next = p_curr + v_next * dist
            
            # Generate arc points
            v_bisect = v_prev + v_next
            bisect_norm = np.linalg.norm(v_bisect)
            if bisect_norm < 1e-9:
                # Vectors are nearly opposite, just add the corner point
                new_points.append(p_curr)
                continue
            v_bisect /= bisect_norm
            
            dist_center = actual_radius / np.sin(angle / 2.0)
            center = p_curr + v_bisect * dist_center
            
            v_center_prev = t_prev - center
            start_angle = np.arctan2(v_center_prev[1], v_center_prev[0])
            
            v_center_next = t_next - center
            end_angle = np.arctan2(v_center_next[1], v_center_next[0])
            
            diff_angle = end_angle - start_angle
            if diff_angle > np.pi: diff_angle -= 2*np.pi
            if diff_angle < -np.pi: diff_angle += 2*np.pi
            
            num_arc_points = max(2, int(abs(diff_angle) * 10)) 
            
            for k in range(num_arc_points + 1):
                alpha = start_angle + diff_angle * (k / float(num_arc_points))
                arc_pt = center + np.array([actual_radius * np.cos(alpha), actual_radius * np.sin(alpha)])
                new_points.append(arc_pt)
                
        return new_points


    def _polygon_area(self, points):
        # A = 0.5 * sum(x_i * y_i+1 - x_i+1 * y_i)
        area = 0.0
        n = len(points)
        for i in range(n):
            p1 = points[i]
            p2 = points[(i + 1) % n]
            area += p1[0] * p2[1]
            area -= p2[0] * p1[1]
        return 0.5 * area

    def inset_polygon(self, points, margin):
        """
        Inset a convex polygon (CCW or CW) by a margin.
        """
        original_area = self._polygon_area(points)
        
        # ... (rest of logic) ...
        
        def normalize(v):
            n = np.linalg.norm(v)
            return v / n if n > 1e-9 else v

        new_points = []
        n = len(points)
        
        # Compute edge lines: p + t * dir
        lines = []
        for i in range(n):
            p_curr = points[i]
            p_next = points[(i+1)%n]
            edge_vec = p_next - p_curr
            edge_len = np.linalg.norm(edge_vec)
            if edge_len < 1e-9: continue
            
            tangent = edge_vec / edge_len
            
            # Re-calculating Normal
            # We want "inward" normal.
            centroid = np.mean(points, axis=0)
            midpoint = (p_curr + p_next) / 2
            to_centroid = centroid - midpoint
            
            normal1 = np.array([-tangent[1], tangent[0]])
            if np.dot(normal1, to_centroid) < 0:
                normal = -normal1
            else:
                normal = normal1
                
            # Displaced line point
            p_disp = p_curr + normal * margin
            lines.append((p_disp, tangent))
            
        if len(lines) < 3: return None
        
        # Compute intersections of offset lines
        for i in range(len(lines)):
            p1, t1 = lines[i]
            p2, t2 = lines[(i+1)%len(lines)]
            
            A = np.array([t1, -t2]).T
            b = p2 - p1
            try:
                x = np.linalg.solve(A, b)
                s = x[0]
                inter_pt = p1 + s * t1
                new_points.append(inter_pt)
            except np.linalg.LinAlgError:
                return None 
                
        # VALIDITY CHECKS
        # 1. Check winding / Area sign
        new_area = self._polygon_area(new_points)
        if abs(new_area) < 1e-9:
             return None # Collapsed
             
        # If original and new area have different signs, it inverted -> Invalid
        if np.sign(original_area) != np.sign(new_area):
            return None
            
        # 2. Check overlap logic or size reduction
        # If new area > original area, something is wrong (since we are insetting)
        if abs(new_area) > abs(original_area):
             return None

        return new_points

    @classmethod
    def import_ods(cls, path):
        return import_ods_2d(cls, path)

    export_ods = export_ods_2d

    def copy(self):
        return copy.deepcopy(self)

    def get_geomentry_table(self):
        table = Table()
        table.insert_row(
            [
                "",
                "Ribs",
                "Chord",
                "X",
                "Y",
                "%",
                "Arc",
                "Arc_diff",
                "AOA",
                "Z-rotation",
                "Y-rotation",
                "profile-merge",
                "ballooning-merge",
            ]
        )
        shape = self.shape.get_half_shape()
        for rib_no in range(self.shape.half_rib_num):
            table[1 + rib_no, 1] = rib_no + 1

        for rib_no, chord in enumerate(shape.chords):
            table[1 + rib_no, 2] = chord

        for rib_no, p in enumerate(self.shape.baseline):
            table[1 + rib_no, 3] = p[0]
            table[1 + rib_no, 4] = p[1]
            table[1 + rib_no, 5] = self.shape.baseline_pos

        last_angle = 0
        for cell_no, angle in enumerate(self.get_arc_angles()):
            angle = angle * 180 / math.pi
            table[1 + cell_no, 6] = angle
            table[1 + cell_no, 7] = angle - last_angle
            last_angle = angle

        for rib_no, aoa in enumerate(self.get_aoa()):
            table[1 + rib_no, 8] = aoa * 180 / math.pi
            table[1 + rib_no, 9] = 0
            table[1 + rib_no, 10] = 0

        return table

    @property
    def arc_positions(self):
        return self.arc.get_arc_positions(self.shape.rib_x_values)

    def get_arc_angles(self, arc_curve=None):
        """
        Get rib rotations
        :param arc_curve:
        :return: rotation angles
        """
        # arc_curve = ArcCurve(self.arc)
        arc_curve = self.arc

        return arc_curve.get_rib_angles(self.shape.rib_x_values)

    @property
    def attachment_points(self):
        """coordinates of the attachment_points"""
        return [
            a_p.get_2D(self.shape)
            for a_p in self.lineset.nodes
            if isinstance(a_p, UpperNode2D)
        ]

    def merge_ballooning(self, factor):
        factor = max(0, min(len(self.balloonings) - 1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.balloonings[i]
        if k > 0:
            second = self.balloonings[i + 1]
            return first * (1 - k) + second * k
        else:
            return first.copy()

    def get_merge_profile(self, factor):
        factor = max(0, min(len(self.profiles) - 1, factor))
        k = factor % 1
        i = int(factor // 1)
        first = self.profiles[i].copy()
        if k > 0:
            second = self.profiles[i + 1]
            airfoil = first * (1 - k) + second * k
        else:
            airfoil = first
        return Profile2D(airfoil.data)

    def get_panels(self, glider_3d=None):
        """
        Create Panels Objects and apply on gliders cells if provided, otherwise create a list of panels
        :param glider_3d: (optional)
        :return: list of "cells"
        """

        def is_greater(cut_1, cut_2):
            if cut_1["left"] >= cut_2["left"] and cut_1["right"] >= cut_2["left"]:
                return True
            return False

        if glider_3d is None:
            cells = [[] for _ in range(self.shape.half_cell_num)]
        else:
            cells = [cell.panels for cell in glider_3d.cells]
            for cell in cells:
                cell = []

        for cell_no, panel_lst in enumerate(cells):
            _cuts = self.elements.get("cuts", [])
            cuts = [cut.copy() for cut in _cuts if cell_no in cut["cells"]]
            for cut in cuts:
                cut.pop("cells")

            # add trailing edge (2x)
            all_values = [c["left"] for c in cuts] + [c["right"] for c in cuts]

            if -1 not in all_values:
                cuts.append({"type": "parallel", "left": -1, "right": -1})
            if 1 not in all_values:
                cuts.append({"type": "parallel", "left": 1, "right": 1})

            cuts.sort(key=lambda cut: cut["left"])

            for cut1, cut2 in ZipCmp(cuts):
                part_no = len(panel_lst)

                if cut1["right"] > cut2["right"]:
                    error_str = "Invalid cut: C{} {:.02f}/{:.02f}/{} + {:.02f}/{:.02f}/{}".format(
                        cell_no + 1,
                        cut1["left"],
                        cut1["right"],
                        cut1["type"],
                        cut2["left"],
                        cut2["right"],
                        cut2["type"],
                    )
                    raise ValueError(error_str)

                if (
                    cut1["type"] == cut2["type"] == "folded"
                    or cut1["type"] == cut2["type"] == "singleskin"
                ):
                    # entry
                    continue

                try:
                    material_code = self.elements["materials"][cell_no][part_no]
                except (KeyError, IndexError):
                    material_code = "unknown"

                panel = Panel(
                    cut1,
                    cut2,
                    name="c{}p{}".format(cell_no + 1, part_no + 1),
                    material_code=material_code,
                )
                panel_lst.append(panel)

        return cells

    def _get_cell_straps(self, name, _cls):
        elements = []
        for cell_no in range(self.shape.half_cell_num):
            cell_elements = []
            for strap in self.elements.get(name, []):
                if cell_no in strap["cells"]:
                    dct = strap.copy()
                    dct.pop("cells")
                    cell_elements.append(_cls(**dct))

            cell_elements.sort(key=lambda strap: strap.get_average_x())

            for strap_no, strap in enumerate(cell_elements):
                strap.name = "c{}{}{}".format(cell_no + 1, name[0], strap_no)

            elements.append(cell_elements)

        return elements

    def get_cell_diagonals(self):
        return self._get_cell_straps("diagonals", DiagonalRib)

    def get_cell_straps(self):
        return self._get_cell_straps("straps", TensionStrap)

    def get_cell_tension_lines(self):
        return self._get_cell_straps("tension_lines", TensionLine)

    def apply_diagonals(self, glider):
        cell_straps = self.get_cell_straps()
        cell_diagonals = self.get_cell_diagonals()
        cell_tensionlines = self.get_cell_tension_lines()

        for cell_no, cell in enumerate(glider.cells):
            cell.diagonals = cell_diagonals[cell_no]
            cell.straps = cell_straps[cell_no]
            cell.straps += cell_tensionlines[cell_no]

    @classmethod
    def fit_glider_3d(cls, glider, numpoints=3):
        return fit_glider_3d(cls, glider, numpoints)

    def get_front_line(self):
        """
        Get Nose Positions for cells
        :return:
        """

    def get_aoa(self, interpolation_num=None):
        aoa_interpolation = self.aoa.interpolation(
            num=interpolation_num or self.num_interpolate
        )

        return [aoa_interpolation(x) for x in self.shape.rib_x_values]

    def apply_aoa(self, glider, interpolation_num=50):
        aoa_interpolation = self.aoa.interpolation(num=interpolation_num)
        aoa_values = [aoa_interpolation(x) for x in self.shape.rib_x_values]

        if self.shape.has_center_cell:
            aoa_values.insert(0, aoa_values[0])

        for rib, aoa in zip(glider.ribs, aoa_values):
            rib.aoa_relative = aoa

    def get_profile_merge(self):
        profile_merge_curve = self.profile_merge_curve.interpolation(
            num=self.num_interpolate
        )
        return [profile_merge_curve(abs(x)) for x in self.shape.rib_x_values]

    def get_ballooning_merge(self):
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(
            num=self.num_interpolate
        )
        return [ballooning_merge_curve(abs(x) for x in self.shape.cell_x_values)]

    def apply_shape_and_arc(self, glider):
        x_values = self.shape.rib_x_values
        shape_ribs = self.shape.ribs
        arc_pos = list(self.arc.get_arc_positions(x_values))
        offset_x = shape_ribs[0][0][1]

        line = []
        chords = []

        for rib_no, x in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]
            startpoint = np.array([-front[1] + offset_x, arc[0], arc[1]])

            line.append(startpoint)
            chords.append(abs(front[1] - back[1]))

        if self.shape.has_center_cell:
            line.insert(0, line[0] * [1, -1, 1])
            chords.insert(0, chords[0])

        for rib_no, p in enumerate(line):
            glider.ribs[rib_no].pos = p
            glider.ribs[rib_no].chord = chords[rib_no]

    def get_glider_3d(self, glider=None, num=50, num_profile=None):
        """returns a new glider from parametric values"""
        glider = glider or Glider()
        ribs = []

        self.rescale_curves()

        x_values = self.shape.rib_x_values
        shape_ribs = self.shape.ribs

        profile_merge_curve = self.profile_merge_curve.interpolation(num=num)
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(num=num)
        aoa_int = self.aoa.interpolation(num=num)
        zrot_int = self.zrot.interpolation(num=num)

        arc_pos = list(self.arc.get_arc_positions(x_values))
        rib_angles = self.arc.get_rib_angles(x_values)

        if self.num_profile is not None:
            num_profile = self.num_profile

        if num_profile is not None:
            profile_x_values = Distribution.from_cos_distribution(num_profile)
        else:
            profile_x_values = self.profiles[0].x_values

        rib_holes = self.elements.get("holes", [])
        rigids = self.elements.get("rigidfoils", [])

        cell_centers = [(p1 + p2) / 2 for p1, p2 in zip(x_values[:-1], x_values[1:])]
        offset_x = shape_ribs[0][0][1]

        rib_material = None
        if "rib_material" in self.elements:
            rib_material = self.elements["rib_material"]

        for rib_no, pos in enumerate(x_values):
            front, back = shape_ribs[rib_no]
            arc = arc_pos[rib_no]
            startpoint = np.array([-front[1] + offset_x, arc[0], arc[1]])

            chord = abs(front[1] - back[1])
            factor = profile_merge_curve(abs(pos))
            profile = self.get_merge_profile(factor)
            profile.name = "Profile{}".format(rib_no)
            profile.x_values = profile_x_values

            this_rib_holes = []
            this_rigid_foils = [
                RigidFoil(rigid["start"], rigid["end"], rigid["distance"])
                for rigid in rigids
                if rib_no in rigid["ribs"]
            ]

            ribs.append(
                Rib(
                    profile_2d=profile,
                    startpoint=startpoint,
                    chord=chord,
                    arcang=rib_angles[rib_no],
                    glide=self.glide,
                    aoa_absolute=aoa_int(pos),
                    zrot=zrot_int(pos),
                    holes=this_rib_holes,
                    rigidfoils=this_rigid_foils,
                    name="rib{}".format(rib_no),
                    material_code=rib_material,
                )
            )
            ribs[-1].aoa_relative = aoa_int(pos)

        if self.shape.has_center_cell:
            new_rib = ribs[0].copy()
            new_rib.name = "rib0"
            new_rib.mirror()
            new_rib.mirrored_rib = ribs[0]
            ribs.insert(0, new_rib)
            cell_centers.insert(0, 0.0)

        glider.cells = []
        for cell_no, (rib1, rib2) in enumerate(zip(ribs[:-1], ribs[1:])):
            ballooning_factor = ballooning_merge_curve(cell_centers[cell_no])
            ballooning = self.merge_ballooning(ballooning_factor)

            cell = Cell(rib1, rib2, ballooning, name="c{}".format(cell_no + 1))

            glider.cells.append(cell)

        glider.close_rib()

        # CELL-ELEMENTS
        self.get_panels(glider)
        self.apply_diagonals(glider)

        for minirib in self.elements.get("miniribs", []):
            data = minirib.copy()
            cells = data.pop("cells")
            
            # Apply global minirib hole settings if enabled
            if getattr(self, 'minirib_holes', False):
                data['num_holes'] = getattr(self, 'minirib_num_holes', 1)
                data['hole_width'] = getattr(self, 'minirib_hole_width', 0.5)
                data['hole_height'] = getattr(self, 'minirib_hole_height', 0.7)
                data['hole_shape'] = getattr(self, 'minirib_hole_shape', 0)
                data['hole_corner_radius'] = getattr(self, 'minirib_hole_corner_radius', 0.25)
                data['hole_max_pos'] = getattr(self, 'minirib_hole_max_pos', 0.9)
            else:
                data['num_holes'] = 0  # Disable holes
            
            for cell_no in cells:
                glider.cells[cell_no].miniribs.append(MiniRib(**data))

        for rigidfoil in self.elements.get("cell_rigidfoils", []):
            data = rigidfoil.copy()
            for cell_no in data.pop("cells"):
                glider.cells[cell_no].rigidfoils.append(PanelRigidFoil(**data))

        # RIB-ELEMENTS

        glider.rename_parts()

        glider.lineset = self.lineset.return_lineset(glider, self.v_inf)
        self.apply_holes(glider)
        self.apply_reinforcements(glider)
        self.apply_rod_sleeves(glider)
        glider.lineset.glider = glider

        glider.lineset.calculate_sag = False
        for _ in range(3):
            glider.lineset.recalc()
        glider.lineset.calculate_sag = True
        glider.lineset.recalc()

        return glider

    def apply_ballooning(self, glider3d):
        for ballooning in self.balloonings:
            ballooning.apply_splines()
        cell_centers = self.shape.cell_x_values
        ballooning_merge_curve = self.ballooning_merge_curve.interpolation(
            num=self.num_interpolate
        )
        for cell_no, cell in enumerate(glider3d.cells):
            ballooning_factor = ballooning_merge_curve(cell_centers[cell_no])
            ballooning = self.merge_ballooning(ballooning_factor)
            cell.ballooning = ballooning

        return glider3d

    @property
    def v_inf(self):
        angle = np.arctan(1 / self.glide)
        return np.array([np.cos(angle), 0, np.sin(angle)]) * self.speed

    def set_area(self, area):
        factor = math.sqrt(area / self.shape.area)
        self.shape.scale(factor)
        self.lineset.scale(factor, scale_lower_floor=False)
        self.rescale_curves()

    def set_aspect_ratio(self, aspect_ratio, remain_area=True):
        ar0 = self.shape.aspect_ratio
        area0 = self.shape.area

        self.shape.scale(y=ar0 / aspect_ratio)

        for p in self.lineset.get_lower_attachment_points():
            p.pos_2D[1] *= ar0 / aspect_ratio

        if remain_area:
            self.set_area(area0)

        return self.shape.aspect_ratio

    ##############################################################
    # is this used?
    def scale(self, x=1, y=1):
        self.shape.scale(x, y)
        if x != 1:
            self.rescale_curves()

    ##############################################################

    def rescale_curves(self):
        span = self.shape.span

        def rescale(curve):
            span_orig = curve.controlpoints[-1][0]
            factor = span / span_orig
            curve._data[:, 0] *= factor

        rescale(self.ballooning_merge_curve)
        rescale(self.profile_merge_curve)
        rescale(self.aoa)
        rescale(self.zrot)
        self.arc.rescale(self.shape.rib_x_values)

    def get_line_bbox(self):
        points = []
        for point in self.lineset.nodes:
            points.append(point.get_2D(self.shape))

        return [
            [min([p[0] for p in points]), min([p[1] for p in points])],
            [max([p[0] for p in points]), max([p[1] for p in points])],
        ]

    def export_lines2D_as_svg(self, file_name=None):
        # sollte im lineset2D sein, aber des lineset hat keine moeglichkeit auf diese Klasse
        # zuzugreifen...
        border = 0.1
        bbox = self.get_line_bbox()
        width = bbox[1][0] - bbox[0][0]
        height = bbox[1][1] - bbox[0][1]

        import svgwrite
        import svgwrite.container

        drawing = svgwrite.Drawing(size=[800, 800 * height / width])

        drawing.viewbox(
            bbox[0][0] - border * width,
            -bbox[1][1] - border * height,
            width * (1 + 2 * border),
            height * (1 + 2 * border),
        )
        lines = svgwrite.container.Group()
        lines.scale(1, -1)
        for line in self.lineset.lines:
            p1 = line.lower_node.get_2D(self.shape)
            p2 = line.upper_node.get_2D(self.shape)
            drawing_line = drawing.polyline(
                [p1, p2],
                style="stroke:black; vector-effect: fill: none; stroke-width:0.01px",
            )
            lines.add(drawing_line)
        drawing.add(lines)

        ribs = svgwrite.container.Group()

        ribs.scale(1, -1)
        p1_old, p2_old = None, None
        for rib in self.shape.ribs:
            p1 = rib[0]
            p2 = rib[1]
            ribs.add(
                drawing.polyline(
                    [p1, p2],
                    style="stroke:black; vector-effect: fill: none; stroke-width:0.01px",
                )
            )
            if p1_old and p2_old:
                ribs.add(
                    drawing.polyline(
                        [p1_old, p1],
                        style="stroke:black; vector-effect: fill: none; stroke-width:0.01px",
                    )
                )
                ribs.add(
                    drawing.polyline(
                        [p2_old, p2],
                        style="stroke:black; vector-effect: fill: none; stroke-width:0.01px",
                    )
                )
            p1_old, p2_old = p1, p2

        drawing.add(ribs)
        if file_name:
            drawing.saveas(file_name)
        return drawing.tostring()
