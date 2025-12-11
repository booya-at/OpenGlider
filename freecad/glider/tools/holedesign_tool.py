from .tools import BaseTool, Line_old
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from openglider.glider.rib import RibHole
from openglider.utils.geometry import is_inside_triangle
import numpy as np
from pivy import coin
import os

class HoleDesignTool(BaseTool):
    widget_name = "Hole Design"

    def __init__(self, obj):
        super(HoleDesignTool, self).__init__(obj)

        # UI Elements with parent widget specified
        self.ribTypeComboBox = QtGui.QComboBox(self.base_widget)
        self.holeShapeComboBox = QtGui.QComboBox(self.base_widget)
        self.numHolesSpinBox = QtGui.QSpinBox(self.base_widget)
        self.holeWidthSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.holeHeightSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.holeHeightModeComboBox = QtGui.QComboBox(self.base_widget)
        self.holeMarginSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.verticalShiftSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.minPosSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.maxPosSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.holeCornerRadiusSpinBox = QtGui.QDoubleSpinBox(self.base_widget)

        # Controls for no-hole zones on suspended ribs
        self.noHoleZoneLabel = QtGui.QLabel("<b>No-Hole Zone Geometry</b>", self.base_widget)
        self.noHoleAngleSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.noHoleBaseWidthSpinBox = QtGui.QDoubleSpinBox(self.base_widget)

        self.applyButton = QtGui.QPushButton("Apply", self.base_widget)

        self.preview_root = coin.SoSeparator()
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        # Add items to combo box
        self.ribTypeComboBox.addItems(["Non-Suspended", "Suspended"])
        self.holeShapeComboBox.addItems(["Ellipse", "Rounded Rectangle"])
        self.holeHeightModeComboBox.addItems(["Percentage", "Margin (mm)"])

        # Add widgets to the QFormLayout provided by BaseTool
        self.layout.addRow("Rib Type", self.ribTypeComboBox)
        self.layout.addRow("Hole Shape", self.holeShapeComboBox)
        self.layout.addRow("Number of Holes", self.numHolesSpinBox)
        self.layout.addRow("Hole Width (%)", self.holeWidthSpinBox)
        self.layout.addRow("Height Mode", self.holeHeightModeComboBox)
        self.layout.addRow("Hole Height (%)", self.holeHeightSpinBox)
        self.layout.addRow("Hole Margin (m)", self.holeMarginSpinBox)
        self.layout.addRow("Vertical Shift (%)", self.verticalShiftSpinBox)
        self.layout.addRow("Min Position (%)", self.minPosSpinBox)
        self.layout.addRow("Max Position (%)", self.maxPosSpinBox)
        self.layout.addRow("Corner Radius (mm)", self.holeCornerRadiusSpinBox)

        # Add separator and controls for no-hole zones
        self.layout.addRow(self.noHoleZoneLabel)
        self.layout.addRow("Angle (deg)", self.noHoleAngleSpinBox)
        self.layout.addRow("Base Width (mm)", self.noHoleBaseWidthSpinBox)

        # Right-align the apply button
        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.applyButton)
        self.layout.addRow(button_layout)

        # Configure spinboxes
        for spinbox in [self.holeWidthSpinBox, self.holeHeightSpinBox, self.verticalShiftSpinBox]:
            spinbox.setSingleStep(0.01)
            spinbox.setDecimals(3)
            spinbox.setMinimum(0.0)
            spinbox.setMaximum(1.0) # Relative to chord

        # Margin spinbox (in mm)
        self.holeMarginSpinBox.setSingleStep(1.0) # 1mm steps
        self.holeMarginSpinBox.setDecimals(1)
        self.holeMarginSpinBox.setSuffix(" mm")
        self.holeMarginSpinBox.setRange(0.0, 1000.0) # Reasonable max margin

        # Corner radius spinbox (as percentage 0-50%)
        self.holeCornerRadiusSpinBox.setSingleStep(1.0) # 1% steps
        self.holeCornerRadiusSpinBox.setDecimals(0)
        self.holeCornerRadiusSpinBox.setSuffix(" %")
        self.holeCornerRadiusSpinBox.setRange(0.0, 50.0) # Max 50% = half the smallest dimension

        # Suspension Hole controls
        self.suspHoleNumSpinBox = QtGui.QSpinBox(self.base_widget)
        self.suspHoleNumSpinBox.setRange(0, 20)
        self.layout.addRow(QtGui.QLabel("Suspension Holes:", self.base_widget), self.suspHoleNumSpinBox)

        self.suspHoleMarginSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.suspHoleMarginSpinBox.setSingleStep(1.0) # 1mm steps
        self.suspHoleMarginSpinBox.setDecimals(1)
        self.suspHoleMarginSpinBox.setSuffix(" mm")
        self.suspHoleMarginSpinBox.setRange(0.0, 100.0) # Reasonable max margin
        self.layout.addRow(QtGui.QLabel("Susp. Hole Margin:", self.base_widget), self.suspHoleMarginSpinBox)

        self.suspHoleRadiusTopSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.suspHoleRadiusTopSpinBox.setSingleStep(1.0) # 1mm steps
        self.suspHoleRadiusTopSpinBox.setDecimals(1)
        self.suspHoleRadiusTopSpinBox.setSuffix(" mm")
        self.suspHoleRadiusTopSpinBox.setRange(0.0, 50.0)
        self.layout.addRow(QtGui.QLabel("Top Radius:", self.base_widget), self.suspHoleRadiusTopSpinBox)

        self.suspHoleRadiusBottomSpinBox = QtGui.QDoubleSpinBox(self.base_widget)
        self.suspHoleRadiusBottomSpinBox.setSingleStep(1.0) # 1mm steps
        self.suspHoleRadiusBottomSpinBox.setDecimals(1)
        self.suspHoleRadiusBottomSpinBox.setSuffix(" mm")
        self.suspHoleRadiusBottomSpinBox.setRange(0.0, 50.0)
        self.layout.addRow(QtGui.QLabel("Bottom Radius:", self.base_widget), self.suspHoleRadiusBottomSpinBox)

        for spinbox in [self.minPosSpinBox, self.maxPosSpinBox]:
            spinbox.setSingleStep(0.01)
            spinbox.setDecimals(3)
            spinbox.setMinimum(0.0)
            spinbox.setMaximum(1.0) # Relative to chord

        self.noHoleAngleSpinBox.setSingleStep(1.0)
        self.noHoleAngleSpinBox.setMinimum(0)
        self.noHoleAngleSpinBox.setMaximum(90)

        self.noHoleBaseWidthSpinBox.setSingleStep(1.0)
        self.noHoleBaseWidthSpinBox.setDecimals(1)
        self.noHoleBaseWidthSpinBox.setSuffix(" mm")
        self.noHoleBaseWidthSpinBox.setRange(0.0, 200.0)  # 0 = full triangle, >0 = truncated

        # Load initial values
        self.update_form_from_glider_data()

        # Connections
        self.ribTypeComboBox.currentIndexChanged.connect(self.on_rib_type_change)
        self.holeShapeComboBox.currentIndexChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.numHolesSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.holeWidthSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.holeHeightModeComboBox.currentIndexChanged.connect(self.on_height_mode_change)
        self.holeHeightSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.holeMarginSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.verticalShiftSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.minPosSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.maxPosSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.holeCornerRadiusSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.noHoleAngleSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.noHoleBaseWidthSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.suspHoleNumSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.suspHoleMarginSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.suspHoleRadiusTopSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.suspHoleRadiusBottomSpinBox.valueChanged.connect(lambda: self.update_glider_data_and_preview(switch=False))
        self.applyButton.clicked.connect(self.accept)

        # Set initial visibility of no-hole zone controls
        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        self.noHoleZoneLabel.setVisible(is_suspended)
        self.noHoleAngleSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.noHoleAngleSpinBox).setVisible(is_suspended)
        self.noHoleBaseWidthSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.noHoleBaseWidthSpinBox).setVisible(is_suspended)
        
        # Initial visibility of susp hole controls
        self.suspHoleNumSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleNumSpinBox).setVisible(is_suspended)
        self.suspHoleMarginSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleMarginSpinBox).setVisible(is_suspended)
        self.suspHoleRadiusTopSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleRadiusTopSpinBox).setVisible(is_suspended)
        self.suspHoleRadiusBottomSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleRadiusBottomSpinBox).setVisible(is_suspended)


    def setup_pivy(self):
        self.task_separator.addChild(self.preview_root)
        self.update_preview()
        Gui.SendMsgToActiveView("ViewFit")

    def get_representative_rib(self, suspended=False):
        """Get a representative rib for preview.
        
        For suspended ribs, ensures the rib has valid attachment points (< 90% chord)
        to avoid counting stabilo/brake-only ribs as suspended.
        """
        glider_instance = self.obj.Proxy.getGliderInstance()
        suspended_ribs = {att.rib for att in glider_instance.lineset.attachment_points if hasattr(att, 'rib')}
        
        if suspended:
            # Find a suspended rib that has valid attachment points (< 90%)
            for rib in glider_instance.ribs:
                if rib in suspended_ribs:
                    all_aps = glider_instance.get_rib_attachment_points(rib)
                    valid_aps = [ap for ap in all_aps if ap.rib_pos <= 0.90]
                    if valid_aps:
                        return rib
            return glider_instance.ribs[0] if glider_instance.ribs else None
        else:
            # Find a non-suspended rib (no attachment points, or only brake attachments)
            for rib in glider_instance.ribs:
                if rib not in suspended_ribs:
                    return rib
                # Also consider ribs with only brake attachments as non-suspended for holes
                all_aps = glider_instance.get_rib_attachment_points(rib)
                valid_aps = [ap for ap in all_aps if ap.rib_pos <= 0.90]
                if not valid_aps:
                    return rib
            return glider_instance.ribs[0] if glider_instance.ribs else None

    def on_height_mode_change(self, index):
        is_margin = index == 1
        self.holeHeightSpinBox.setVisible(not is_margin)
        self.layout.labelForField(self.holeHeightSpinBox).setVisible(not is_margin)
        self.holeMarginSpinBox.setVisible(is_margin)
        self.layout.labelForField(self.holeMarginSpinBox).setVisible(is_margin)
        self.update_glider_data_and_preview(switch=False)

    def on_rib_type_change(self, new_index):
        # Save the data of the previous tab before switching
        previous_index = 1 - new_index
        self.update_glider_data(is_suspended=previous_index == 1)

        is_suspended = new_index == 1

        # Show/hide no-hole zone controls
        self.noHoleZoneLabel.setVisible(is_suspended)
        self.noHoleAngleSpinBox.setVisible(is_suspended)
        # Also hide the labels associated with the spinboxes
        self.layout.labelForField(self.noHoleAngleSpinBox).setVisible(is_suspended)
        self.noHoleBaseWidthSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.noHoleBaseWidthSpinBox).setVisible(is_suspended)
        
        self.suspHoleNumSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleNumSpinBox).setVisible(is_suspended)
        self.suspHoleMarginSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleMarginSpinBox).setVisible(is_suspended)
        self.suspHoleRadiusTopSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleRadiusTopSpinBox).setVisible(is_suspended)
        self.suspHoleRadiusBottomSpinBox.setVisible(is_suspended)
        self.layout.labelForField(self.suspHoleRadiusBottomSpinBox).setVisible(is_suspended)

        # Then, load the values for the newly selected rib type
        self.update_form_from_glider_data()
        self.update_preview()

    def update_preview(self, *args):
        self.preview_root.removeAllChildren()

        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        rib = self.get_representative_rib(suspended=is_suspended)
        if not rib: return

        profile_points = list(rib.profile_2d.data)
        self.preview_root.addChild(Line_old(profile_points + [profile_points[0]], width=2).object)

        no_hole_zones = []
        if is_suspended:
            glider_instance = self.obj.Proxy.getGliderInstance()
            attachment_points = glider_instance.get_rib_attachment_points(rib)
            for ap in attachment_points:
                # Visualize attachment point
                ap_pos_on_surface = rib.profile_2d.align([ap.rib_pos, -1.0])
                marker = coin.SoSeparator()
                trans = coin.SoTranslation()
                trans.translation.setValue(ap_pos_on_surface[0], ap_pos_on_surface[1], 0)
                mat = coin.SoMaterial()
                mat.diffuseColor.setValue(1, 0, 0) # Red
                sphere = coin.SoSphere()
                sphere.radius = 0.005
                marker.addChild(trans)
                marker.addChild(mat)
                marker.addChild(sphere)
                self.preview_root.addChild(marker)

                # Define and draw no-hole zones
                angle = self.noHoleAngleSpinBox.value()
                v1 = ap_pos_on_surface # Apex on intrados

                angle_rad = np.deg2rad(angle)

                upper_point = rib.profile_2d.align([ap.rib_pos, 1.0])
                local_vertical = upper_point - v1
                if np.linalg.norm(local_vertical) < 1e-9: continue
                local_vertical /= np.linalg.norm(local_vertical)

                angle_offset = np.arctan2(local_vertical[1], local_vertical[0])

                dir2 = np.array([np.cos(angle_offset - angle_rad), np.sin(angle_offset - angle_rad)])
                dir3 = np.array([np.cos(angle_offset + angle_rad), np.sin(angle_offset + angle_rad)])

                extrados_poly = rib.profile_2d.get_extrados_poly()

                # Use a very large number to ensure the line cuts through the extrados
                far_factor = rib.chord * 100

                v2 = extrados_poly.line_intersection(v1, v1 + dir2 * far_factor)
                v3 = extrados_poly.line_intersection(v1, v1 + dir3 * far_factor)

                if v2 is not None and v3 is not None:
                    # Get base width for truncated triangle (trapezoid)
                    base_width_m = self.noHoleBaseWidthSpinBox.value() / 1000.0  # mm to m
                    base_width_norm = base_width_m / rib.chord  # normalize to chord
                    
                    print(f"DEBUG: base_width_norm={base_width_norm}, base_width_m={base_width_m}")
                    
                    if base_width_norm > 1e-6:
                        # Create trapezoid by cutting off the apex (v1) with a horizontal line
                        # The base width defines the width of the flat bottom
                        
                        # Calculate the height offset to get desired base width
                        # Using similar triangles: base_width / top_width = cut_height / total_height
                        top_width = np.linalg.norm(v2 - v3)  # Distance between extrados intersections
                        triangle_height = np.linalg.norm(local_vertical)  # Approximate height
                        
                        if top_width > 1e-9:
                            # Cut ratio determines how far up from v1 we cut
                            # At cut_ratio=0, base_width=0; at cut_ratio=1, base_width=top_width
                            cut_ratio = base_width_norm / top_width if top_width > 0 else 0
                            cut_ratio = min(cut_ratio, 0.9)  # Limit to avoid going past v2/v3
                            
                            # Points on edges at cut_ratio from apex
                            v1_left = v1 + (v2 - v1) * cut_ratio
                            v1_right = v1 + (v3 - v1) * cut_ratio
                            
                            # Trapezoid: v1_left -> v2 -> v3 -> v1_right -> v1_left
                            no_hole_zones.append((v1_left, v2, v3, v1_right))
                            zone_points = [v1_left, v2, v3, v1_right, v1_left]
                            self.preview_root.addChild(Line_old(zone_points, color='red', width=1).object)
                        else:
                            # Fallback to triangle
                            no_hole_zones.append((v1, v2, v3))
                            zone_points = [v1, v2, v3, v1]
                            self.preview_root.addChild(Line_old(zone_points, color='red', width=1).object)
                    else:
                        # Full triangle (no truncation)
                        no_hole_zones.append((v1, v2, v3))
                        zone_points = [v1, v2, v3, v1]
                        self.preview_root.addChild(Line_old(zone_points, color='red', width=1).object)
                    
                    # PREVIEW TRUSS HOLES
                    susp_hole_num = self.suspHoleNumSpinBox.value()
                    susp_hole_margin = self.suspHoleMarginSpinBox.value() / 1000.0 # to meters
                    susp_hole_radius_top = self.suspHoleRadiusTopSpinBox.value() / 1000.0 # to meters
                    susp_hole_radius_bottom = self.suspHoleRadiusBottomSpinBox.value() / 1000.0 # to meters
                    
                    if susp_hole_num > 0:
                        truss_holes = self.parametric_glider.generate_truss_holes(
                            rib, v1, v2, v3, 
                            susp_hole_num, 
                            susp_hole_margin, 
                            radius_top=susp_hole_radius_top,
                            radius_bottom=susp_hole_radius_bottom
                        )
                        for poly in truss_holes:
                             closed_poly = list(poly)
                             if len(closed_poly) > 0 and (closed_poly[0] != closed_poly[-1]).any():
                                 closed_poly.append(closed_poly[0])
                             self.preview_root.addChild(Line_old(closed_poly, color='green', width=1).object)
                    

        # Get current parameters from the UI
        num_holes = self.numHolesSpinBox.value()
        hole_width_perc = self.holeWidthSpinBox.value()
        hole_height_perc = self.holeHeightSpinBox.value()
        hole_height_mode = self.holeHeightModeComboBox.currentIndex()
        hole_margin_m = self.holeMarginSpinBox.value() / 1000.0 # Convert mm to m for usage
        vertical_shift_perc = self.verticalShiftSpinBox.value()
        hole_shape_index = self.holeShapeComboBox.currentIndex()
        min_pos = self.minPosSpinBox.value()
        max_pos = self.maxPosSpinBox.value()

        if num_holes == 0:
            return

        allowed_ranges = [(min_pos, max_pos)]

        # Visualize Airfoil Structure elements (rod sleeves and reinforcements)
        pg = self.parametric_glider
        glider_instance = self.obj.Proxy.getGliderInstance()
        rib_idx = glider_instance.ribs.index(rib) if rib in glider_instance.ribs else 0
        
        # Draw rod sleeves from configuration
        from openglider.glider.rib.elements import RodSleeve
        suffix = '_s' if is_suspended else '_ns'
        
        # Draw extrados sleeves
        extrados_enabled = getattr(pg, f'extrados_sleeves_enabled{suffix}', True)
        extrados_configs = getattr(pg, f'extrados_sleeves{suffix}', [])
        print(f"DEBUG: extrados_enabled={extrados_enabled}, configs={len(extrados_configs)}, suffix={suffix}")
        if extrados_enabled and extrados_configs:
            for config in extrados_configs:
                excluded_ribs = config.get('excluded_ribs', [])
                if rib_idx not in excluded_ribs:
                    try:
                        sleeve = RodSleeve(
                            surface='extrados',
                            width=config.get('width', 0.015),
                            offset=config.get('offset', 0.005),
                            start_chord=config.get('start_chord', 0.0),
                            end_chord=config.get('end_chord', 0.7),
                        )
                        inner_pts, outer_pts = sleeve.get_sleeve_points(rib)
                        if inner_pts and outer_pts:
                            inner_norm = [[p[0]/rib.chord, p[1]/rib.chord] for p in inner_pts]
                            outer_norm = [[p[0]/rib.chord, p[1]/rib.chord] for p in outer_pts]
                            sleeve_poly = inner_norm + list(reversed(outer_norm)) + [inner_norm[0]]
                            self.preview_root.addChild(Line_old(sleeve_poly, color='green', width=2).object)
                    except Exception as e:
                        import traceback
                        print(f"Error drawing extrados sleeve: {e}")
                        traceback.print_exc()
        
        # Draw intrados sleeves
        intrados_enabled = getattr(pg, f'intrados_sleeves_enabled{suffix}', True)
        intrados_configs = getattr(pg, f'intrados_sleeves{suffix}', [])
        print(f"DEBUG: intrados_enabled={intrados_enabled}, configs={len(intrados_configs)}, suffix={suffix}")
        if intrados_enabled and intrados_configs:
            for config in intrados_configs:
                excluded_ribs = config.get('excluded_ribs', [])
                if rib_idx not in excluded_ribs:
                    try:
                        sleeve = RodSleeve(
                            surface='intrados',
                            width=config.get('width', 0.015),
                            offset=config.get('offset', 0.005),
                            start_chord=config.get('start_chord', 0.06),
                            end_chord=config.get('end_chord', 0.5),
                        )
                        inner_pts, outer_pts = sleeve.get_sleeve_points(rib)
                        if inner_pts and outer_pts:
                            inner_norm = [[p[0]/rib.chord, p[1]/rib.chord] for p in inner_pts]
                            outer_norm = [[p[0]/rib.chord, p[1]/rib.chord] for p in outer_pts]
                            sleeve_poly = inner_norm + list(reversed(outer_norm)) + [inner_norm[0]]
                            self.preview_root.addChild(Line_old(sleeve_poly, color='white', width=2).object)
                    except Exception as e:
                        import traceback
                        print(f"Error drawing intrados sleeve: {e}")
                        traceback.print_exc()
        
        # Draw reinforcements if they exist for this rib (suspended only)
        if is_suspended and hasattr(rib, 'reinforcements') and rib.reinforcements:
            for reinf in rib.reinforcements:
                try:
                    halfmoon_pts = reinf.get_halfmoon_points(rib)
                    if halfmoon_pts:
                        # Normalize by chord for preview
                        halfmoon_norm = [[p[0]/rib.chord, p[1]/rib.chord] for p in halfmoon_pts]
                        self.preview_root.addChild(Line_old(halfmoon_norm, color='yellow', width=2).object)
                except Exception as e:
                    print(f"Error drawing reinforcement: {e}")

        # Distribute holes across the allowed ranges
        total_allowable_length = sum(end - start for start, end in allowed_ranges)
        if total_allowable_length <= 1e-6:
            return

        # A more robust way to distribute N holes across M ranges
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
                upper_point = rib.profile_2d.profilepoint(-pos_x)
                lower_point = rib.profile_2d.profilepoint(pos_x)
                local_thickness = upper_point[1] - lower_point[1]
                if local_thickness < 1e-6:
                    continue

                new_lower_bound = lower_point
                if is_suspended:
                    hole_center_x = (upper_point[0] + lower_point[0]) / 2.0
                    min_y_ceiling = upper_point[1]

                    for v1, v2, v3 in no_hole_zones:
                        if min(v1[0], v2[0], v3[0]) <= hole_center_x <= max(v1[0], v2[0], v3[0]):
                            for p1, p2 in [(v1, v2), (v2, v3), (v3, v1)]:
                                if p1[0] != p2[0] and ((p1[0] <= hole_center_x <= p2[0]) or (p2[0] <= hole_center_x <= p1[0])):
                                    y_intersect = p1[1] + (p2[1] - p1[1]) * (hole_center_x - p1[0]) / (p2[0] - p1[0])
                                    if y_intersect < min_y_ceiling:
                                        min_y_ceiling = min(min_y_ceiling, y_intersect)

                    available_height = min_y_ceiling - lower_point[1]
                    hole_center = np.array([hole_center_x, lower_point[1] + available_height / 2])
                    
                    # Apply vertical shift within available height
                    hole_center[1] += available_height / 2 * vertical_shift_perc
                    
                else:
                    available_height = upper_point[1] - lower_point[1]
                    hole_center = lower_point + (upper_point - lower_point) / 2 * (1 + vertical_shift_perc)

                if available_height < 1e-4:
                    continue
                
                if hole_height_mode == 1: # Margin mode
                    hole_height = available_height - 2 * hole_margin_m
                else: # Percent mode
                    hole_height = hole_height_perc * available_height
                
                hole_width = hole_width_perc * rib.chord

                if hole_height <= 0 or hole_width <= 0:
                    continue

                if hole_shape_index == 0: # Ellipse
                    shape_points = []
                    for angle in np.linspace(0, 2 * np.pi, 50):
                        x = hole_width / 2 * np.cos(angle)
                        y = hole_height / 2 * np.sin(angle)
                        shape_points.append([x, y])
                else: # Rounded Rectangle
                    corner_radius_ratio = self.holeCornerRadiusSpinBox.value() / 100.0 # Convert % to ratio
                    shape_points = self.create_rounded_rectangle(hole_width, hole_height, corner_radius_ratio)

                shape_poly = np.array(shape_points)
                shape_poly += hole_center

                shape_points_closed = list(shape_poly)
                self.preview_root.addChild(Line_old(shape_points_closed + [shape_points_closed[0]], color='blue').object)

    def create_rounded_rectangle(self, width, height, corner_radius_ratio=0.25):
        # corner_radius_ratio is a ratio of min(width, height)
        radius = min(width, height) * corner_radius_ratio
        if radius > width / 2.0: radius = width / 2.0
        if radius > height / 2.0: radius = height / 2.0
        
        w = width / 2 - radius
        h = height / 2 - radius

        points = []
        # Top right corner
        for angle in np.linspace(0, np.pi/2, 10):
            points.append((w + radius * np.cos(angle), h + radius * np.sin(angle)))
        # Top left corner
        for angle in np.linspace(np.pi/2, np.pi, 10):
            points.append((-w + radius * np.cos(angle), h + radius * np.sin(angle)))
        # Bottom left corner
        for angle in np.linspace(np.pi, 3*np.pi/2, 10):
            points.append((-w + radius * np.cos(angle), -h + radius * np.sin(angle)))
        # Bottom right corner
        for angle in np.linspace(3*np.pi/2, 2*np.pi, 10):
            points.append((w + radius * np.cos(angle), -h + radius * np.sin(angle)))
            
        points.append(points[0]) # Close the loop

        return points

    def update_form_from_glider_data(self):
        pg = self.parametric_glider
        is_suspended = self.ribTypeComboBox.currentIndex() == 1

        suffix = "_s" if is_suspended else "_ns"

        widgets_to_block = [self.holeShapeComboBox, self.numHolesSpinBox, self.holeWidthSpinBox,
                            self.holeHeightSpinBox, self.verticalShiftSpinBox,
                            self.minPosSpinBox, self.maxPosSpinBox,
                            self.holeHeightModeComboBox, self.holeMarginSpinBox, self.holeCornerRadiusSpinBox]
        if is_suspended:
            widgets_to_block.extend([self.noHoleAngleSpinBox, self.noHoleBaseWidthSpinBox, self.suspHoleNumSpinBox, self.suspHoleMarginSpinBox, self.suspHoleRadiusTopSpinBox, self.suspHoleRadiusBottomSpinBox])

        # Block signals to prevent feedback loops
        for widget in widgets_to_block:
            widget.blockSignals(True)

        self.holeShapeComboBox.setCurrentIndex(getattr(pg, f'hole_shape{suffix}', 0))
        self.numHolesSpinBox.setValue(getattr(pg, f'num_holes{suffix}', 30))
        self.holeWidthSpinBox.setValue(getattr(pg, f'hole_width{suffix}', 0.003))
        self.holeHeightSpinBox.setValue(getattr(pg, f'hole_height{suffix}', 0.8))
        self.verticalShiftSpinBox.setValue(getattr(pg, f'vertical_shift{suffix}', 0.0))
        self.minPosSpinBox.setValue(getattr(pg, f'min_hole_pos{suffix}', 0.2))
        self.maxPosSpinBox.setValue(getattr(pg, f'max_hole_pos{suffix}', 0.8))
        self.holeHeightModeComboBox.setCurrentIndex(getattr(pg, f'hole_height_mode{suffix}', 0))
        self.holeMarginSpinBox.setValue(getattr(pg, f'hole_margin{suffix}', 0.02) * 1000.0) # Convert m to mm for UI
        self.holeCornerRadiusSpinBox.setValue(getattr(pg, f'hole_corner_radius{suffix}', 0.25) * 100.0) # Convert ratio to % for UI

        if is_suspended:
            self.noHoleAngleSpinBox.setValue(getattr(pg, 'hole_free_angle_s', 30.0))
            self.noHoleBaseWidthSpinBox.setValue(getattr(pg, 'hole_base_width_s', 0.0))  # in mm
            self.suspHoleNumSpinBox.setValue(getattr(pg, 'susp_hole_num_s', 3))
            self.suspHoleMarginSpinBox.setValue(getattr(pg, 'susp_hole_margin_s', 0.01) * 1000.0)
            self.suspHoleRadiusTopSpinBox.setValue(getattr(pg, 'susp_hole_radius_top_s', 0.005) * 1000.0)
            self.suspHoleRadiusBottomSpinBox.setValue(getattr(pg, 'susp_hole_radius_bottom_s', 0.005) * 1000.0)

        # Initial visibility update
        self.on_height_mode_change(self.holeHeightModeComboBox.currentIndex())

        # Unblock signals
        for widget in widgets_to_block:
            widget.blockSignals(False)

    def update_glider_data(self, is_suspended):
        pg = self.parametric_glider
        if is_suspended:
            pg.hole_shape_s = self.holeShapeComboBox.currentIndex()
            pg.num_holes_s = self.numHolesSpinBox.value()
            pg.hole_width_s = self.holeWidthSpinBox.value()
            pg.hole_height_s = self.holeHeightSpinBox.value()
            pg.vertical_shift_s = self.verticalShiftSpinBox.value()
            pg.min_hole_pos_s = self.minPosSpinBox.value()
            pg.max_hole_pos_s = self.maxPosSpinBox.value()
            pg.hole_free_angle_s = self.noHoleAngleSpinBox.value()
            pg.hole_base_width_s = self.noHoleBaseWidthSpinBox.value()  # store in mm
            pg.hole_height_mode_s = self.holeHeightModeComboBox.currentIndex()
            pg.hole_margin_s = self.holeMarginSpinBox.value() / 1000.0 # Convert mm to m for storage
            pg.susp_hole_num_s = self.suspHoleNumSpinBox.value()
            pg.susp_hole_margin_s = self.suspHoleMarginSpinBox.value() / 1000.0
            pg.susp_hole_radius_top_s = self.suspHoleRadiusTopSpinBox.value() / 1000.0
            pg.susp_hole_radius_bottom_s = self.suspHoleRadiusBottomSpinBox.value() / 1000.0
            pg.hole_corner_radius_s = self.holeCornerRadiusSpinBox.value() / 100.0 # Convert % to ratio
        else:
            pg.hole_shape_ns = self.holeShapeComboBox.currentIndex()
            pg.num_holes_ns = self.numHolesSpinBox.value()
            pg.hole_width_ns = self.holeWidthSpinBox.value()
            pg.hole_height_ns = self.holeHeightSpinBox.value()
            pg.vertical_shift_ns = self.verticalShiftSpinBox.value()
            pg.min_hole_pos_ns = self.minPosSpinBox.value()
            pg.max_hole_pos_ns = self.maxPosSpinBox.value()
            pg.hole_height_mode_ns = self.holeHeightModeComboBox.currentIndex()
            pg.hole_margin_ns = self.holeMarginSpinBox.value() / 1000.0 # Convert mm to m for storage
            pg.hole_corner_radius_ns = self.holeCornerRadiusSpinBox.value() / 100.0 # Convert % to ratio

    def update_glider_data_and_preview(self, *args, switch=False):
        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        self.update_glider_data(is_suspended)
        self.update_preview()

    def accept(self):
        # When accepting, save the data from the currently visible tab.
        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        self.update_glider_data(is_suspended)
        self.update_view_glider()
        super(HoleDesignTool, self).accept()
