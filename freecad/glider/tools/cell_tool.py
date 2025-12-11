from __future__ import division

from pivy import coin

from PySide import QtGui

from .glider import draw_glider, draw_lines
from .tools import BaseTool, input_field
from .table import base_table_widget


def refresh():
    pass


class CellTool(BaseTool):
    hide = True
    turn = False

    # Default parameters for auto-generation
    DIAGONAL_HALF_WIDTH = 0.02  # 2cm half-width (4cm total)
    DIAGONAL_EXTRADOS_OFFSET = 0.0  # No offset from top of extrados
    VECTOR_STRAP_WIDTH = 0.04  # 4cm width

    def __init__(self, obj):
        super(CellTool, self).__init__(obj)
        self.diagonals_table = diagonals_table()
        self.diagonals_table.get_from_ParametricGlider(self.parametric_glider)
        self.diagonals_button = QtGui.QPushButton("diagonals")
        self.diagonals_button.clicked.connect(self.diagonals_table.show)
        self.layout.setWidget(0, input_field, self.diagonals_button)

        self.vector_table = vector_table()
        self.vector_table.get_from_ParametricGlider(self.parametric_glider)
        self.vector_button = QtGui.QPushButton("vector strap")
        self.vector_button.clicked.connect(self.vector_table.show)
        self.layout.setWidget(1, input_field, self.vector_button)

        self.update_button = QtGui.QPushButton("update glider")
        self.update_button.clicked.connect(self.update_glider)
        self.layout.setWidget(2, input_field, self.update_button)

        # Auto-fill buttons
        self.auto_diagonals_button = QtGui.QPushButton("Auto-fill Diagonals")
        self.auto_diagonals_button.clicked.connect(self.auto_fill_diagonals)
        self.layout.setWidget(3, input_field, self.auto_diagonals_button)

        self.auto_straps_button = QtGui.QPushButton("Auto-fill Vector Straps")
        self.auto_straps_button.clicked.connect(self.auto_fill_vector_straps)
        self.layout.setWidget(4, input_field, self.auto_straps_button)

        self.draw_glider()

    def draw_glider(self):
        _rot = coin.SbRotation()
        _rot.setValue(coin.SbVec3f(0, 1, 0), coin.SbVec3f(1, 0, 0))
        rot = coin.SoRotation()
        rot.rotation.setValue(_rot)
        self.task_separator += rot
        draw_glider(
            self.parametric_glider.get_glider_3d(),
            self.task_separator,
            hull=None,
            ribs=True,
            fill_ribs=False,
        )
        draw_lines(
            self.parametric_glider.get_glider_3d(),
            vis_lines=self.task_separator,
            line_num=1,
        )

    def update_glider(self):
        self.task_separator.removeAllChildren()
        self.apply_elements()
        self.draw_glider()

    def apply_elements(self):
        self.diagonals_table.apply_to_glider(self.parametric_glider)
        self.vector_table.apply_to_glider(self.parametric_glider)

    def accept(self):
        super(CellTool, self).accept()
        self.diagonals_table.hide()
        self.vector_table.hide()
        del self.diagonals_table
        del self.vector_table
        self.update_view_glider()

    def reject(self):
        super(CellTool, self).reject()
        self.diagonals_table.hide()
        self.vector_table.hide()
        del self.diagonals_table
        del self.vector_table

    def _get_suspended_ribs(self, exclude_brake=True):
        """
        Get set of rib indices that have suspension attachment points.
        Returns dict mapping rib_no -> list of attachment point positions.
        """
        lineset = self.parametric_glider.lineset
        upper_nodes = lineset.get_upper_nodes()
        
        # Map rib_no to attachment positions
        # For UpperNode2D: cell_no is the cell, cell_pos determines if on left (0) or right (1) rib
        # rib_no = cell_no when cell_pos=0 (left rib of cell)
        rib_attachments = {}
        for node in upper_nodes:
            # Skip brake/stabilo lines
            if exclude_brake:
                layer = (node.layer or "").lower()
                if layer in ("brake", "stabilo", "s", "frein", "f"):
                    continue
            
            # Calculate actual rib number
            # cell_no is 0-indexed, cell_pos is usually 0
            # Attachment on left rib of cell N means rib N
            rib_no = node.cell_no + int(node.cell_pos)
            
            if rib_no not in rib_attachments:
                rib_attachments[rib_no] = []
            rib_attachments[rib_no].append(node.rib_pos)
        
        return rib_attachments

    def _get_cell_count(self):
        """Get total number of cells (half-span)."""
        return self.parametric_glider.shape.half_cell_num

    def _get_suspended_ribs_with_layer(self):
        """
        Get attachment points with their line layer (A, B, C, D, etc.).
        Returns dict mapping rib_no -> list of (rib_pos, layer) tuples.
        """
        lineset = self.parametric_glider.lineset
        upper_nodes = lineset.get_upper_nodes()
        
        rib_attachments = {}
        for node in upper_nodes:
            layer = (node.layer or "").upper()
            # Skip brake/stabilo lines
            if layer in ("BRAKE", "STABILO", "S", "FREIN", "F"):
                continue
            
            rib_no = node.cell_no + int(node.cell_pos)
            
            if rib_no not in rib_attachments:
                rib_attachments[rib_no] = []
            rib_attachments[rib_no].append((node.rib_pos, layer))
        
        return rib_attachments


    def auto_fill_diagonals(self):
        """
        Auto-generate diagonal ribs from attachment points.
        Shows configuration dialog with per-line-type parameters.
        """
        # Configuration dialog
        dialog = QtGui.QDialog()
        dialog.setWindowTitle("Configuration des diagonales")
        dialog.setMinimumWidth(550)
        layout = QtGui.QVBoxLayout(dialog)
        
        # Header
        header = QtGui.QLabel("Paramètres par type de ligne")
        header.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header)
        
        # Create table for line parameters
        line_types = ["A", "B", "C", "D"]
        param_table = QtGui.QTableWidget(len(line_types), 3)
        param_table.setHorizontalHeaderLabels([
            "Largeur intrados (cm)",
            "Extrados début (%)",
            "Extrados fin (%)"
        ])
        param_table.setVerticalHeaderLabels(line_types)
        param_table.horizontalHeader().setStretchLastSection(True)
        
        # Default values for each line type
        # (intrados_cm, extrados_start_%, extrados_end_%)
        defaults = {
            "A": (4.0, 5.0, 15.0),
            "B": (4.0, 15.0, 30.0),
            "C": (4.0, 30.0, 50.0),
            "D": (4.0, 50.0, 75.0),
        }
        
        line_spinboxes = {}
        for row, line_type in enumerate(line_types):
            intrados_spin = QtGui.QDoubleSpinBox()
            intrados_spin.setRange(1, 20)
            intrados_spin.setValue(defaults[line_type][0])
            intrados_spin.setSuffix(" cm")
            
            extrados_start_spin = QtGui.QDoubleSpinBox()
            extrados_start_spin.setRange(0, 100)
            extrados_start_spin.setValue(defaults[line_type][1])
            extrados_start_spin.setSuffix(" %")
            
            extrados_end_spin = QtGui.QDoubleSpinBox()
            extrados_end_spin.setRange(0, 100)
            extrados_end_spin.setValue(defaults[line_type][2])
            extrados_end_spin.setSuffix(" %")
            
            param_table.setCellWidget(row, 0, intrados_spin)
            param_table.setCellWidget(row, 1, extrados_start_spin)
            param_table.setCellWidget(row, 2, extrados_end_spin)
            
            line_spinboxes[line_type] = (intrados_spin, extrados_start_spin, extrados_end_spin)
        
        layout.addWidget(param_table)
        
        # Vertical offset for all diagonals (in mm)
        layout.addWidget(QtGui.QLabel(""))
        offset_layout = QtGui.QHBoxLayout()
        offset_layout.addWidget(QtGui.QLabel("Décalage vertical (depuis extrados):"))
        offset_spin = QtGui.QSpinBox()
        offset_spin.setRange(0, 100)
        offset_spin.setValue(0)  # Default 0 mm
        offset_spin.setSuffix(" mm")
        offset_layout.addWidget(offset_spin)
        offset_layout.addStretch()
        layout.addLayout(offset_layout)
        
        # Button box
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return
        
        # Get vertical offset in mm - will be converted per position using real profile thickness
        offset_mm = offset_spin.value()
        
        # Get glider 3D data for profile information
        glider_3d = self.parametric_glider.get_glider_3d()
        
        # Get a reference rib for profile thickness calculation
        # Use middle rib as reference
        ref_rib_index = len(glider_3d.ribs) // 2
        ref_rib = glider_3d.ribs[ref_rib_index]
        ref_chord = ref_rib.chord
        
        print(f"DEBUG: Reference rib {ref_rib_index}, chord = {ref_chord*100:.1f} cm")
        
        # Function to calculate height value for a given x position with offset
        def get_extrados_height_with_offset(x_pos, offset_mm):
            """
            Calculate the height value (0-1 range for extrados) considering the offset.
            Uses real profile thickness at the given x position.
            """
            if offset_mm == 0:
                return 1.0
            
            profile = ref_rib.profile_2d
            try:
                # Get upper and lower points at this x position
                upper_point = profile.profilepoint(x_pos, h=1.0)
                lower_point = profile.profilepoint(x_pos, h=-1.0)
                
                # Local thickness in profile units (0-1 normalized)
                local_thickness_normalized = upper_point[1] - lower_point[1]
                
                # Convert to real thickness in cm
                local_thickness_cm = local_thickness_normalized * ref_chord * 100
                
                if local_thickness_cm < 0.1:
                    return 1.0  # Very thin, no offset
                
                # Height reduction: offset_mm / (local_thickness_cm * 10) gives fraction,
                # multiply by 2 for height range (-1 to 1)
                offset_cm = offset_mm / 10.0
                height_reduction = (offset_cm / local_thickness_cm) * 2.0
                
                extrados_height = 1.0 - height_reduction
                return max(0.0, min(1.0, extrados_height))
            except:
                # Fallback to simple calculation
                return 1.0 - offset_mm * 0.005
        
        # Calculate extrados_height at a reference position (middle of chord)
        ref_extrados_height = get_extrados_height_with_offset(0.3, offset_mm)
        print(f"DEBUG: offset_mm={offset_mm}, ref_extrados_height at x=0.3 = {ref_extrados_height:.4f}")
        
        # Get per-line-type parameters
        chord_cm = ref_chord * 100  # Convert to cm
        line_params = {}
        for line_type, (intrados_spin, ext_start_spin, ext_end_spin) in line_spinboxes.items():
            # Convert cm to fraction of chord, % to fraction
            half_width_intrados = (intrados_spin.value() / 2) / chord_cm
            extrados_start = ext_start_spin.value() / 100.0
            extrados_end = ext_end_spin.value() / 100.0
            
            # Calculate extrados height at the middle of the extrados range
            mid_x = (extrados_start + extrados_end) / 2
            ext_height = get_extrados_height_with_offset(mid_x, offset_mm)
            
            line_params[line_type] = {
                "half_intrados": half_width_intrados,
                "extrados_start": extrados_start,
                "extrados_end": extrados_end,
                "extrados_height": ext_height,
            }
        
        print(f"DEBUG: line_params = {line_params}")
        
        # Default params for unknown line types
        default_params = line_params.get("A", {
            "half_intrados": 0.02,
            "extrados_start": 0.05,
            "extrados_end": 0.15,
            "extrados_height": 1.0,
        })
        
        rib_attachments = self._get_suspended_ribs_with_layer()
        cell_count = self._get_cell_count()
        
        # Track which cells have diagonals from which direction
        # cell_diagonals[cell_no] = {"from_left": [...], "from_right": [...]}
        # Each entry is (rib_pos, layer, params)
        cell_diagonals = {i: {"from_left": [], "from_right": []} for i in range(cell_count)}
        
        # Generate diagonals from each attachment point
        for rib_no, attachments in sorted(rib_attachments.items()):
            for rib_pos, layer in attachments:
                # Get params for this line type
                params = line_params.get(layer, default_params)
                
                # Create diagonal to the left cell 
                left_cell = rib_no
                if left_cell >= 0 and left_cell < cell_count:
                    cell_diagonals[left_cell]["from_right"].append((rib_pos, layer, params))
                
                # Create diagonal to the right cell
                right_cell = rib_no + 1
                if right_cell >= 0 and right_cell < cell_count:
                    cell_diagonals[right_cell]["from_left"].append((rib_pos, layer, params))
        
        # Group diagonals by parameters (separate lists for diagonals and bands)
        diagonals_grouped = {}
        bands_grouped = {}
        
        for cell_no in range(cell_count):
            cell_data = cell_diagonals[cell_no]
            
            # Diagonals from left side of cell (attachment on left rib -> goes to right rib extrados)
            for rib_pos, layer, params in cell_data["from_left"]:
                half_bottom = params["half_intrados"]
                ext_start = params["extrados_start"]
                ext_end = params["extrados_end"]
                ext_height = params["extrados_height"]
                
                # Intrados: centered on rib_pos
                # Extrados: from ext_start to ext_end (absolute positions on chord)
                key = (
                    round(ext_start, 4), ext_height,           # right_front (extrados start)
                    round(ext_end, 4), ext_height,             # right_back (extrados end)
                    round(rib_pos + half_bottom, 4), -1.0,     # left_back (intrados)
                    round(rib_pos - half_bottom, 4), -1.0,     # left_front (intrados)
                )
                if key not in diagonals_grouped:
                    diagonals_grouped[key] = []
                diagonals_grouped[key].append(cell_no)
            
            # Diagonals from right side of cell (attachment on right rib -> goes to left rib extrados)
            for rib_pos, layer, params in cell_data["from_right"]:
                half_bottom = params["half_intrados"]
                ext_start = params["extrados_start"]
                ext_end = params["extrados_end"]
                ext_height = params["extrados_height"]
                
                # Intrados: centered on rib_pos
                # Extrados: from ext_start to ext_end (absolute positions on chord)
                key = (
                    round(rib_pos - half_bottom, 4), -1.0,     # right_front (intrados)
                    round(rib_pos + half_bottom, 4), -1.0,     # right_back (intrados)
                    round(ext_end, 4), ext_height,             # left_back (extrados end)
                    round(ext_start, 4), ext_height,           # left_front (extrados start)
                )
                if key not in diagonals_grouped:
                    diagonals_grouped[key] = []
                diagonals_grouped[key].append(cell_no)
        
        # Create horizontal bands on cells that need them, PER LINE TYPE
        # Each line type (A, B, C, D) gets its own bands on cells that don't have diagonals of that type
        # Bands connect extrados to extrados (never to intrados)
        
        print(f"DEBUG: Creating bands per line type")
        
        # Track which cells have diagonals of each line type
        # cells_by_layer[layer] = set of cell numbers with diagonals of that layer
        cells_by_layer = {}
        layer_params = {}  # Store params for each layer
        
        for cell_no in range(cell_count):
            cell_data = cell_diagonals[cell_no]
            for diag_list in [cell_data["from_left"], cell_data["from_right"]]:
                for rib_pos, layer, params in diag_list:
                    if layer not in cells_by_layer:
                        cells_by_layer[layer] = set()
                        layer_params[layer] = params  # Store params for this layer
                    cells_by_layer[layer].add(cell_no)
        
        print(f"DEBUG: Line types found: {list(cells_by_layer.keys())}")
        for layer, cells in cells_by_layer.items():
            print(f"DEBUG: Layer {layer}: cells with diagonals = {sorted(cells)}")
        
        # For each line type, find gaps and create bands
        for layer, cells_with_diag in cells_by_layer.items():
            params = layer_params[layer]
            ext_start = params["extrados_start"]
            ext_end = params["extrados_end"]
            ext_height = params["extrados_height"]
            
            # Find cells that DON'T have diagonals of this layer
            for cell_no in range(cell_count):
                if cell_no in cells_with_diag:
                    continue  # This cell has a diagonal of this layer, skip
                
                # Check if there are neighboring cells with this layer's diagonals
                # (to know if we need a band here)
                has_left_neighbor = (cell_no - 1) in cells_with_diag if cell_no > 0 else False
                has_right_neighbor = (cell_no + 1) in cells_with_diag if cell_no < cell_count - 1 else False
                
                # Only create band if there are diagonals on both sides (gap to fill)
                # OR if there's at least one neighbor with this layer
                if has_left_neighbor or has_right_neighbor:
                    print(f"DEBUG: Band on cell {cell_no} for layer {layer}: height={ext_height:.3f}")
                    
                    # Band is horizontal - all 4 corners at same height, same layer
                    band_key = (
                        round(ext_start, 4), ext_height,  # right_front
                        round(ext_end, 4), ext_height,    # right_back
                        round(ext_end, 4), ext_height,    # left_back
                        round(ext_start, 4), ext_height,  # left_front
                    )
                    if band_key not in bands_grouped:
                        bands_grouped[band_key] = []
                    if cell_no not in bands_grouped[band_key]:
                        bands_grouped[band_key].append(cell_no)
        
        print(f"DEBUG: Total diagonals: {len(diagonals_grouped)}, bands: {len(bands_grouped)}")
        
        # Convert grouped diagonals to list format
        diagonals = []
        for key, cells in diagonals_grouped.items():
            diag = {
                "right_front": (key[0], key[1]),
                "right_back": (key[2], key[3]),
                "left_back": (key[4], key[5]),
                "left_front": (key[6], key[7]),
                "cells": sorted(set(cells)),
            }
            diagonals.append(diag)
        
        # Add bands as SEPARATE entries (all 4 heights same)
        for key, cells in bands_grouped.items():
            band = {
                "right_front": (key[0], key[1]),
                "right_back": (key[2], key[3]),
                "left_back": (key[4], key[5]),
                "left_front": (key[6], key[7]),
                "cells": sorted(set(cells)),
            }
            diagonals.append(band)
        
        print(f"DEBUG: Total entries in table: {len(diagonals)}")
        
        # Sort by position
        diagonals.sort(key=lambda d: (d["cells"][0] if d["cells"] else 0, d["right_front"][0]))
        
        # Populate the diagonals table
        self.diagonals_table.set_diagonals(diagonals)
        self.diagonals_table.show()

    def auto_fill_vector_straps(self):
        """
        Auto-generate vector straps connecting intrados attachment points.
        Shows configuration dialog first to get parameters.
        """
        # Configuration dialog
        dialog = QtGui.QDialog()
        dialog.setWindowTitle("Configuration des bandes de tension")
        layout = QtGui.QFormLayout(dialog)
        
        # Width in mm
        width_spin = QtGui.QSpinBox()
        width_spin.setRange(10, 100)
        width_spin.setValue(40)
        width_spin.setSuffix(" mm")
        layout.addRow("Largeur des bandes:", width_spin)
        
        # Button box
        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return
        
        # Get width value (convert mm to fraction)
        width_mm = width_spin.value()
        half_width = (width_mm / 2) / 1000.0
        
        # Get attachment points (excluding brake lines)
        rib_attachments = self._get_suspended_ribs(exclude_brake=True)
        cell_count = self._get_cell_count()
        
        # Collect all unique positions and their rib locations
        position_tolerance = 0.02  # 2% tolerance for grouping
        
        all_positions = []
        for rib_no, positions in rib_attachments.items():
            for pos in positions:
                all_positions.append((rib_no, pos))
        
        # Sort by position
        all_positions.sort(key=lambda x: x[1])
        
        # Group similar positions
        position_groups = []
        used = set()
        for rib_no, pos in all_positions:
            if (rib_no, pos) in used:
                continue
            
            # Find all positions close to this one
            group = [(rib_no, pos)]
            used.add((rib_no, pos))
            
            for other_rib, other_pos in all_positions:
                if (other_rib, other_pos) not in used:
                    if abs(other_pos - pos) < position_tolerance:
                        group.append((other_rib, other_pos))
                        used.add((other_rib, other_pos))
            
            position_groups.append(group)
        
        # Use dict to group straps by center position
        straps_grouped = {}
        width = half_width * 2  # Full width for storage
        
        # Create straps for each position group
        for group in position_groups:
            if len(group) < 2:
                continue  # Need at least 2 points to create a strap
            
            # Get average position (rounded) - this is the center
            avg_pos = round(sum(p[1] for p in group) / len(group), 4)
            
            # Get max rib (straps go from center/cell 0 to this rib)
            rib_nos = [p[0] for p in group]
            max_rib = max(rib_nos)
            
            # Key is center position
            key = avg_pos
            if key not in straps_grouped:
                straps_grouped[key] = []
            
            # Cells go from 0 (center) to max_rib
            for cell_no in range(0, min(max_rib, cell_count)):
                if cell_no not in straps_grouped[key]:
                    straps_grouped[key].append(cell_no)
        
        # Convert to list format with width
        straps = []
        for center_pos, cells in straps_grouped.items():
            if cells:
                strap = {
                    "left": center_pos,  # Center position
                    "right": center_pos, # Same position on both sides
                    "width": width,      # Width in profile fraction
                    "cells": sorted(set(cells)),
                }
                straps.append(strap)
        
        # Sort by position
        straps.sort(key=lambda s: s["left"])
        
        # Populate the vector straps table
        self.vector_table.set_straps(straps)
        self.vector_table.show()


def number_input(number):
    return QtGui.QTableWidgetItem(str(number))


class diagonals_table(base_table_widget):
    name = "diagonals"
    keyword = "diagonals"

    def __init__(self):
        super(diagonals_table, self).__init__(name="diagonals")
        self.table.setRowCount(200)
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            [
                "right\nfront",
                "rf\nheight",
                "right\nback",
                "rb\nheight",
                "left\nback",
                "lb\nheight",
                "left\nfront",
                "lf\nheight",
                "cells",
            ]
        )

    def get_from_ParametricGlider(self, ParametricGlider):
        if "diagonals" in ParametricGlider.elements:
            diags = ParametricGlider.elements["diagonals"]
            for row, element in enumerate(diags):
                entries = list(
                    element["right_front"]
                    + element["right_back"]
                    + element["left_back"]
                    + element["left_front"]
                )
                entries.append(element["cells"])
                self.table.setRow(row, entries)

    def apply_to_glider(self, ParametricGlider):
        num_rows = self.table.rowCount()
        # remove all diagonals from the glide_2d
        ParametricGlider.elements[self.keyword] = []
        for n_row in range(num_rows):
            row = self.get_row(n_row)
            if row:
                diagonal = {}
                diagonal["right_front"] = (row[0], row[1])
                diagonal["right_back"] = (row[2], row[3])
                diagonal["left_back"] = (row[4], row[5])
                diagonal["left_front"] = (row[6], row[7])
                diagonal["cells"] = row[-1]
                ParametricGlider.elements["diagonals"].append(diagonal)

    def set_diagonals(self, diagonals_list):
        """Populate table with auto-generated diagonals."""
        # Clear existing rows
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setText("")
        
        # Fill with new data
        for row, element in enumerate(diagonals_list):
            # Format: rf_x, rf_h, rb_x, rb_h, lb_x, lb_h, lf_x, lf_h, cells
            rf = element["right_front"]
            rb = element["right_back"]
            lb = element["left_back"]
            lf = element["left_front"]
            cells_str = ",".join(map(str, element["cells"]))
            
            entries = [rf[0], rf[1], rb[0], rb[1], lb[0], lb[1], lf[0], lf[1], cells_str]
            for col, value in enumerate(entries):
                self.table.setItem(row, col, value)

    def get_row(self, n_row):
        str_row = []
        for i in range(9):
            item = self.table.item(n_row, i)
            if item:
                text = item.text()
                if text and text.strip():
                    # Replace comma with dot for decimal separator
                    str_row.append(text.strip().replace(",", "."))
        
        if len(str_row) != 9:
            return None
        try:
            return list(map(float, str_row[:-1])) + [
                list(map(int, str_row[-1].replace(".", ",").split(",")))
            ]
        except (TypeError, ValueError) as e:
            print(e)
            print("something wrong with row " + str(n_row))
            return None


class vector_table(base_table_widget):
    def __init__(self):
        super(vector_table, self).__init__(name="vector straps")
        self.table.setRowCount(200)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["left", "right", "width", "cells"])

    def get_from_ParametricGlider(self, ParametricGlider):
        # Try straps first, then tension_lines for backwards compatibility
        straps = ParametricGlider.elements.get("straps", [])
        if not straps:
            straps = ParametricGlider.elements.get("tension_lines", [])
        
        for row, element in enumerate(straps):
            left = element.get("left", element.get("center_left", 0))
            right = element.get("right", element.get("center_right", 0))
            width = element.get("width", 0.04)  # Default 40mm
            entries = [left, right, width, element["cells"]]
            self.table.setRow(row, entries)

    def apply_to_glider(self, ParametricGlider):
        num_rows = self.table.rowCount()
        # Use 'straps' keyword for TensionStrap objects with width
        ParametricGlider.elements["straps"] = []
        for n_row in range(num_rows):
            row = self.get_row(n_row)
            if row:
                strap = {
                    "left": row[0],
                    "right": row[1],
                    "width": row[2],
                    "cells": row[3],
                }
                ParametricGlider.elements["straps"].append(strap)

    def set_straps(self, straps_list):
        """Populate table with auto-generated vector straps."""
        # Clear existing rows
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setText("")
        
        # Fill with new data
        for row, element in enumerate(straps_list):
            cells_str = ",".join(map(str, element["cells"]))
            entries = [element["left"], element["right"], element["width"], cells_str]
            for col, value in enumerate(entries):
                self.table.setItem(row, col, value)

    def get_row(self, n_row):
        str_row = []
        for i in range(4):
            item = self.table.item(n_row, i)
            if item:
                text = item.text()
                if text and text.strip():
                    # Replace comma with dot for decimal separator
                    str_row.append(text.strip().replace(",", "."))
        
        if len(str_row) != 4:
            return None
        try:
            return list(map(float, str_row[:-1])) + [
                list(map(int, str_row[-1].replace(".", ",").split(",")))
            ]
        except (TypeError, ValueError) as e:
            print("something wrong with row " + str(n_row))
            return None
