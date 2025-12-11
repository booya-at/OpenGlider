"""
Lines Auto-Placement Dialog for OpenGlider

This dialog allows users to automatically generate suspension line attachment points
and line architecture based on configurable parameters.

Architecture concept:
- Lines are organized by TYPE (A, B, C, D, F) along the chord
- Within each type, lines are organized by GROUPS along the span
- Each GROUP corresponds to ONE "basse" (lower line connecting to riser)
- Each group can have its own pattern (3:1, 2:2:1, etc.)

Example for A lines with 6 attachment points:
- Group 1 (A1): pattern 3:1 → 3 hautes connect to basse A1
- Group 2 (A2): pattern 2:2:1 → 2+2 hautes connect via inters to basse A2
"""

from __future__ import division

import numpy as np
from PySide import QtCore, QtGui

from openglider.glider.parametric.lines import (
    BatchNode2D,
    Line2D,
    LineSet2D,
    LowerNode2D,
    UpperNode2D,
)
from openglider.lines.line_types import LineType


class GroupPatternWidget(QtGui.QWidget):
    """Widget for defining pattern per group."""
    
    PATTERNS = ["1:1", "2:1", "3:1", "2:2:1", "3:2:1", "4:2:1"]
    
    def __init__(self, parent=None):
        super(GroupPatternWidget, self).__init__(parent)
        layout = QtGui.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Pattern input as text
        self.pattern_edit = QtGui.QLineEdit()
        self.pattern_edit.setPlaceholderText("ex: 3:1, 2:2:1, 2:1, 2:1")
        self.pattern_edit.setText("2:1")
        layout.addWidget(self.pattern_edit)
        
        # Help label
        help_label = QtGui.QLabel("Format: pattern1, pattern2, ... (répété si besoin)")
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(help_label)
    
    def get_patterns(self):
        """Parse pattern string and return list of patterns."""
        text = self.pattern_edit.text().strip()
        if not text:
            return [[2]]  # Default 2:1
        
        patterns = []
        for part in text.split(","):
            part = part.strip()
            if ":" in part:
                try:
                    pattern = [int(x) for x in part.split(":") if x.strip() and x.strip() != "1"]
                    if not pattern:
                        pattern = [1]
                    patterns.append(pattern)
                except ValueError:
                    patterns.append([2])  # Default
            else:
                try:
                    patterns.append([int(part)])
                except ValueError:
                    patterns.append([2])
        
        return patterns if patterns else [[2]]


class LineTypeConfigRow(QtGui.QWidget):
    """Widget for configuring a single line type (A, B, C, D, F)."""
    
    configChanged = QtCore.Signal()
    
    def __init__(self, line_type_name, default_position, default_pattern="2:1", parent=None):
        super(LineTypeConfigRow, self).__init__(parent)
        self.line_type_name = line_type_name
        
        layout = QtGui.QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        
        # Enable checkbox
        self.enable_checkbox = QtGui.QCheckBox(line_type_name)
        self.enable_checkbox.setChecked(True)
        self.enable_checkbox.setFixedWidth(40)
        layout.addWidget(self.enable_checkbox)
        
        # Position (%)
        self.position_spinbox = QtGui.QDoubleSpinBox()
        self.position_spinbox.setRange(0, 100)
        self.position_spinbox.setValue(default_position)
        self.position_spinbox.setDecimals(1)
        self.position_spinbox.setSuffix("%")
        self.position_spinbox.setFixedWidth(65)
        layout.addWidget(self.position_spinbox)
        
        # Interval
        self.interval_spinbox = QtGui.QSpinBox()
        self.interval_spinbox.setRange(1, 10)
        self.interval_spinbox.setValue(1)
        self.interval_spinbox.setPrefix("/")
        self.interval_spinbox.setFixedWidth(45)
        layout.addWidget(self.interval_spinbox)
        
        # Start cell
        self.start_spinbox = QtGui.QSpinBox()
        self.start_spinbox.setRange(0, 50)
        self.start_spinbox.setValue(0)
        self.start_spinbox.setPrefix("@")
        self.start_spinbox.setFixedWidth(45)
        layout.addWidget(self.start_spinbox)
        
        # Group patterns (text input)
        self.patterns_edit = QtGui.QLineEdit()
        self.patterns_edit.setPlaceholderText("2:1, 3:1, ...")
        self.patterns_edit.setText(default_pattern)
        self.patterns_edit.setFixedWidth(120)
        layout.addWidget(self.patterns_edit)
        
        # Connect signals
        self.enable_checkbox.toggled.connect(self._update_enabled_state)
        self.enable_checkbox.toggled.connect(lambda: self.configChanged.emit())
        self.position_spinbox.valueChanged.connect(lambda: self.configChanged.emit())
        self.interval_spinbox.valueChanged.connect(lambda: self.configChanged.emit())
        self.start_spinbox.valueChanged.connect(lambda: self.configChanged.emit())
        self.patterns_edit.textChanged.connect(lambda: self.configChanged.emit())
        
    def _update_enabled_state(self, enabled):
        self.position_spinbox.setEnabled(enabled)
        self.interval_spinbox.setEnabled(enabled)
        self.start_spinbox.setEnabled(enabled)
        self.patterns_edit.setEnabled(enabled)
    
    def is_enabled(self):
        return self.enable_checkbox.isChecked()
    
    def get_group_patterns(self):
        """Parse group patterns from text input."""
        text = self.patterns_edit.text().strip()
        if not text:
            return [[2]]  # Default 2:1
        
        patterns = []
        for part in text.split(","):
            part = part.strip()
            if ":" in part:
                try:
                    # Parse "2:2:1" -> [2, 2] (remove final :1)
                    nums = [int(x) for x in part.split(":") if x.strip()]
                    # Remove trailing 1s (they're implicit)
                    while len(nums) > 1 and nums[-1] == 1:
                        nums.pop()
                    patterns.append(nums if nums else [1])
                except ValueError:
                    patterns.append([2])
            else:
                try:
                    patterns.append([int(part)])
                except ValueError:
                    patterns.append([2])
        
        return patterns if patterns else [[2]]
    
    def get_config(self):
        return {
            "enabled": self.is_enabled(),
            "position": self.position_spinbox.value() / 100.0,
            "interval": self.interval_spinbox.value(),
            "start_cell": self.start_spinbox.value(),
            "group_patterns": self.get_group_patterns(),
        }


class LinesAutoPlacementDialog(QtGui.QDialog):
    """Dialog for automatic placement of suspension lines."""
    
    # Default configurations
    LINE_DEFAULTS = {
        "A": {"position": 8.5, "interval": 1, "pattern": "3:1, 2:2:1"},
        "B": {"position": 27.5, "interval": 2, "pattern": "2:2:1, 2:1"},
        "C": {"position": 53.0, "interval": 2, "pattern": "2:1"},
        "D": {"position": 77.0, "interval": 3, "pattern": "2:1"},
        "F": {"position": 100.0, "interval": 1, "pattern": "1:1"},
    }
    
    def __init__(self, parametric_glider, parent=None):
        super(LinesAutoPlacementDialog, self).__init__(parent)
        self.parametric_glider = parametric_glider
        self.half_cell_num = parametric_glider.shape.half_cell_num
        self.half_rib_num = parametric_glider.shape.half_rib_num
        
        # Calculate span
        try:
            shape = parametric_glider.shape.get_half_shape()
            self.span = abs(shape.front[-1][0] - shape.front[0][0])
        except:
            self.span = 6.0
        
        self.setWindowTitle("Auto-placement des suspentes")
        self.setMinimumWidth(520)
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QtGui.QVBoxLayout(self)
        
        # === Point Pilote ===
        lower_group = QtGui.QGroupBox("Point Pilote (X=envergure, Y=corde, Z=hauteur)")
        lower_layout = QtGui.QFormLayout(lower_group)
        
        # Demi-écartement (X - span direction)
        self.demi_ecartement = QtGui.QDoubleSpinBox()
        self.demi_ecartement.setRange(0, 2.0)
        self.demi_ecartement.setValue(0.2)
        self.demi_ecartement.setSingleStep(0.05)
        self.demi_ecartement.setSuffix(" m")
        lower_layout.addRow("Demi-écartement:", self.demi_ecartement)
        
        # Profondeur (Y - chord direction, from leading edge)
        self.profondeur = QtGui.QDoubleSpinBox()
        self.profondeur.setRange(-5, 5)
        self.profondeur.setValue(0.5)
        self.profondeur.setSingleStep(0.1)
        self.profondeur.setSuffix(" m")
        lower_layout.addRow("Profondeur:", self.profondeur)
        
        # Hauteur cône (Z - height below wing)
        self.hauteur_cone = QtGui.QDoubleSpinBox()
        self.hauteur_cone.setRange(1, 15)
        self.hauteur_cone.setValue(7)
        self.hauteur_cone.setSingleStep(0.5)
        self.hauteur_cone.setSuffix(" m")
        lower_layout.addRow("Hauteur cône:", self.hauteur_cone)
        
        main_layout.addWidget(lower_group)

        
        # === Lengths ===
        lengths_group = QtGui.QGroupBox("Longueurs")
        lengths_layout = QtGui.QFormLayout(lengths_group)
        
        self.riser_length = QtGui.QDoubleSpinBox()
        self.riser_length.setRange(0.1, 2.0)
        self.riser_length.setValue(0.47)
        self.riser_length.setSingleStep(0.01)
        self.riser_length.setSuffix(" m")
        lengths_layout.addRow("Élévateurs:", self.riser_length)
        
        basses_widget = QtGui.QWidget()
        basses_layout = QtGui.QHBoxLayout(basses_widget)
        basses_layout.setContentsMargins(0, 0, 0, 0)
        self.basses_length = QtGui.QDoubleSpinBox()
        self.basses_length.setRange(0.5, 10.0)
        self.basses_length.setValue(round(self.span / 3, 2))
        self.basses_length.setSuffix(" m")
        basses_layout.addWidget(self.basses_length)
        self.basses_auto = QtGui.QCheckBox("Auto")
        self.basses_auto.setChecked(True)
        self.basses_auto.toggled.connect(lambda c: self.basses_length.setEnabled(not c))
        basses_layout.addWidget(self.basses_auto)
        lengths_layout.addRow("Basses:", basses_widget)
        
        inter_widget = QtGui.QWidget()
        inter_layout = QtGui.QHBoxLayout(inter_widget)
        inter_layout.setContentsMargins(0, 0, 0, 0)
        self.inter_length = QtGui.QDoubleSpinBox()
        self.inter_length.setRange(0.5, 10.0)
        self.inter_length.setValue(max(0.5, round(self.span / 3 - 1, 2)))
        self.inter_length.setSuffix(" m")
        inter_layout.addWidget(self.inter_length)
        self.inter_auto = QtGui.QCheckBox("Auto")
        self.inter_auto.setChecked(True)
        self.inter_auto.toggled.connect(lambda c: self.inter_length.setEnabled(not c))
        inter_layout.addWidget(self.inter_auto)
        lengths_layout.addRow("Inter:", inter_widget)
        
        main_layout.addWidget(lengths_group)
        
        # === Line Types ===
        lines_group = QtGui.QGroupBox("Lignes (Type | Pos | /Cell | @Start | Patterns)")
        lines_layout = QtGui.QVBoxLayout(lines_group)
        
        self.line_type_rows = {}
        for lt in ["A", "B", "C", "D", "F"]:
            defaults = self.LINE_DEFAULTS[lt]
            row = LineTypeConfigRow(lt, defaults["position"], defaults["pattern"])
            row.interval_spinbox.setValue(defaults["interval"])
            self.line_type_rows[lt] = row
            lines_layout.addWidget(row)
            row.configChanged.connect(self._update_info)
        
        # Help text
        help_text = QtGui.QLabel("Patterns: 2:1 = 2 hautes→1 basse | 2:2:1 = 2+2 hautes→2 inter→1 basse")
        help_text.setStyleSheet("color: gray; font-size: 10px;")
        lines_layout.addWidget(help_text)
        
        main_layout.addWidget(lines_group)
        
        # === Stabilo ===
        stabilo_group = QtGui.QGroupBox("Stabilo")
        stabilo_layout = QtGui.QFormLayout(stabilo_group)
        
        self.stabilo_checkbox = QtGui.QCheckBox("Inclure")
        self.stabilo_checkbox.setChecked(True)
        stabilo_layout.addRow("", self.stabilo_checkbox)
        
        self.stabilo_position = QtGui.QDoubleSpinBox()
        self.stabilo_position.setRange(0, 100)
        self.stabilo_position.setValue(50)
        self.stabilo_position.setSuffix(" %")
        stabilo_layout.addRow("Position:", self.stabilo_position)
        
        main_layout.addWidget(stabilo_group)
        
        # === Material ===
        material_group = QtGui.QGroupBox("Matériau")
        material_layout = QtGui.QFormLayout(material_group)
        
        self.line_type_combo = QtGui.QComboBox()
        for lt in sorted(LineType.types.keys()):
            self.line_type_combo.addItem(lt)
        idx = self.line_type_combo.findText("default")
        if idx >= 0:
            self.line_type_combo.setCurrentIndex(idx)
        material_layout.addRow("Type:", self.line_type_combo)
        
        main_layout.addWidget(material_group)
        
        # === Buttons ===
        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QtGui.QPushButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        apply_btn = QtGui.QPushButton("Appliquer")
        apply_btn.clicked.connect(self.accept)
        apply_btn.setDefault(True)
        button_layout.addWidget(apply_btn)
        
        main_layout.addLayout(button_layout)
        
        # Info
        self.info_label = QtGui.QLabel("")
        self.info_label.setStyleSheet("color: gray;")
        main_layout.addWidget(self.info_label)
        
        self._update_info()
    
    def _update_info(self):
        if not hasattr(self, 'info_label'):
            return
        count = 0
        groups = 0
        for lt, row in self.line_type_rows.items():
            if row.is_enabled():
                cfg = row.get_config()
                n = len(list(range(cfg["start_cell"], self.half_cell_num, cfg["interval"])))
                count += n
                groups += 1
        if hasattr(self, 'stabilo_checkbox') and self.stabilo_checkbox.isChecked():
            count += 1
        self.info_label.setText(f"Points: {count} | Élévateurs: {groups}")
    
    def get_configuration(self):
        basses = self.basses_length.value()
        if self.basses_auto.isChecked():
            basses = round(self.span / 3, 2)
        inter = self.inter_length.value()
        if self.inter_auto.isChecked():
            inter = max(0.5, basses - 1.0)
        
        return {
            "demi_ecartement": self.demi_ecartement.value(),  # X - span
            "profondeur": self.profondeur.value(),            # Y - chord
            "hauteur_cone": self.hauteur_cone.value(),        # Z - height
            "riser_length": self.riser_length.value(),
            "basses_length": basses,
            "inter_length": inter,
            "line_types": {lt: row.get_config() for lt, row in self.line_type_rows.items()},
            "line_type_name": self.line_type_combo.currentText(),
            "include_stabilo": self.stabilo_checkbox.isChecked(),
            "stabilo_position": self.stabilo_position.value() / 100.0,
        }
    
    def generate_lineset(self):
        """Generate LineSet2D."""
        config = self.get_configuration()
        lines = []
        
        # Point Pilote coordinates (raw values from user)
        # X = profondeur (chord direction)
        # Y = demi-écartement (span direction)  
        # Z = -hauteur_cone (below wing)
        lower_x = config["profondeur"]
        lower_y = config["demi_ecartement"]
        lower_z = -config["hauteur_cone"]
        
        # Single main lower node (point pilote)
        main_lower = LowerNode2D(
            pos_2D=[lower_x, lower_z],
            pos_3D=[lower_x, lower_y, lower_z],
            name="pilote",
            layer="",
        )
        
        # Get enabled types
        enabled = [lt for lt in ["A", "B", "C", "D", "F"] 
                  if config["line_types"][lt]["enabled"]]
        
        # Create riser for each enabled type
        # Spread risers slightly around the pilote X position
        riser_nodes = {}
        riser_spread = 0.15  # Small spread for risers
        
        for i, lt in enumerate(enabled):
            if len(enabled) > 1:
                riser_x = lower_x + (i / (len(enabled) - 1) - 0.5) * riser_spread
            else:
                riser_x = lower_x
            
            riser = BatchNode2D(
                pos_2D=[riser_x, lower_z + config["riser_length"]],
                name=f"riser_{lt}",
                layer=lt,
            )
            riser_nodes[lt] = riser
            lines.append(Line2D(
                lower_node=main_lower,
                upper_node=riser,
                target_length=config["riser_length"],
                line_type=config["line_type_name"],
                layer=lt,
                name=f"riser_{lt}",
            ))
        
        # Generate lines for each type
        for lt in enabled:
            lt_config = config["line_types"][lt]
            upper_nodes = self._generate_upper_nodes(lt, lt_config)
            
            if upper_nodes:
                lt_lines = self._generate_grouped_architecture(
                    upper_nodes=upper_nodes,
                    riser_node=riser_nodes[lt],
                    group_patterns=lt_config["group_patterns"],
                    basses_length=config["basses_length"],
                    inter_length=config["inter_length"],
                    line_type_name=config["line_type_name"],
                    layer=lt,
                )
                lines.extend(lt_lines)
        
        # Stabilo
        if config["include_stabilo"]:
            stabilo_cell = self.half_cell_num - 1
            stabilo = UpperNode2D(
                cell_no=stabilo_cell,
                rib_pos=config["stabilo_position"],
                cell_pos=0,
                force=1.0,
                name="S1",
                layer="S",
            )
            
            # Stabilo riser - position at outer edge
            stab_riser_x = lower_x + riser_spread + 0.1
            stab_riser = BatchNode2D(
                pos_2D=[stab_riser_x, lower_z + config["riser_length"]],
                name="riser_S",
                layer="S",
            )
            lines.append(Line2D(
                lower_node=main_lower,
                upper_node=stab_riser,
                target_length=config["riser_length"],
                line_type=config["line_type_name"],
                layer="S",
                name="riser_S",
            ))
            lines.append(Line2D(
                lower_node=stab_riser,
                upper_node=stabilo,
                target_length=config["basses_length"],
                line_type=config["line_type_name"],
                layer="S",
                name="S1",
            ))
        
        return LineSet2D(lines)
    
    def _generate_upper_nodes(self, line_type, config):
        """Generate upper attachment points."""
        nodes = []
        start = config["start_cell"]
        interval = config["interval"]
        position = config["position"]
        
        idx = 1
        for cell_no in range(start, self.half_cell_num, interval):
            # Ensure cell_no is valid
            if cell_no >= self.half_cell_num:
                break
            node = UpperNode2D(
                cell_no=cell_no,
                rib_pos=position,
                cell_pos=0,
                force=1.0,
                name=f"{line_type}{idx}",
                layer=line_type,
            )
            nodes.append(node)
            idx += 1
        
        return nodes
    
    def _generate_grouped_architecture(self, upper_nodes, riser_node, group_patterns,
                                       basses_length, inter_length, line_type_name, layer):
        """
        Generate architecture with groups.
        Each group = 1 basse connected to riser.
        Pattern defines how hautes connect to basse (via inter if needed).
        """
        lines = []
        
        if not upper_nodes:
            return lines
        
        # Determine how many nodes per group based on patterns
        # Pattern [2] = 2:1, takes 2 nodes per group
        # Pattern [2, 2] = 2:2:1, takes 4 nodes per group
        # Pattern [3] = 3:1, takes 3 nodes per group
        
        node_idx = 0
        group_idx = 0
        
        while node_idx < len(upper_nodes):
            # Get pattern for this group (cycle through patterns)
            pattern = group_patterns[group_idx % len(group_patterns)]
            
            # Calculate how many nodes this pattern consumes
            nodes_per_group = self._calc_nodes_for_pattern(pattern)
            
            # Get nodes for this group
            group_nodes = upper_nodes[node_idx:node_idx + nodes_per_group]
            
            if not group_nodes:
                break
            
            # Create basse node for this group
            basse_pos = self._calc_batch_position(group_nodes, 0)
            basse_pos[1] = basse_pos[1] - 2.0  # Move down
            
            basse_node = BatchNode2D(
                pos_2D=basse_pos,
                name=f"{layer}{group_idx + 1}_basse",
                layer=layer,
            )
            
            # Connect basse to riser
            lines.append(Line2D(
                lower_node=riser_node,
                upper_node=basse_node,
                target_length=basses_length,
                line_type=line_type_name,
                layer=layer,
                name=f"{layer}{group_idx + 1}",
            ))
            
            # Generate architecture within group
            group_lines = self._generate_group_architecture(
                group_nodes, basse_node, pattern, inter_length, line_type_name, layer, group_idx
            )
            lines.extend(group_lines)
            
            node_idx += len(group_nodes)
            group_idx += 1
        
        return lines
    
    def _calc_nodes_for_pattern(self, pattern):
        """Calculate how many upper nodes a pattern consumes."""
        if pattern == [1]:
            return 1
        
        # Pattern [2] = 2 nodes
        # Pattern [2, 2] = 2*2 = 4 nodes
        # Pattern [3] = 3 nodes
        # Pattern [3, 2] = 3*2 = 6 nodes
        result = 1
        for p in pattern:
            result *= p
        return result
    
    def _generate_group_architecture(self, nodes, basse_node, pattern, 
                                    inter_length, line_type_name, layer, group_idx):
        """Generate lines within a group."""
        lines = []
        
        if pattern == [1] or len(nodes) == 1:
            # Direct connection
            for i, node in enumerate(nodes):
                lines.append(Line2D(
                    lower_node=basse_node,
                    upper_node=node,
                    target_length=inter_length,  # This becomes haute length
                    line_type=line_type_name,
                    layer=layer,
                    name=node.name,
                ))
            return lines
        
        if len(pattern) == 1:
            # Simple pattern like 2:1 or 3:1
            merge = pattern[0]
            for i, node in enumerate(nodes):
                lines.append(Line2D(
                    lower_node=basse_node,
                    upper_node=node,
                    target_length=inter_length,
                    line_type=line_type_name,
                    layer=layer,
                    name=node.name,
                ))
            return lines
        
        # Multi-level pattern like 2:2:1
        # First merge by first number, then by second, etc.
        current_nodes = list(nodes)
        
        for level, merge in enumerate(pattern[:-1]):  # All but last (which connects to basse)
            next_nodes = []
            
            for i in range(0, len(current_nodes), merge):
                group = current_nodes[i:i + merge]
                if len(group) == 1:
                    next_nodes.append(group[0])
                    continue
                
                # Create inter node
                inter_pos = self._calc_batch_position(group, level)
                inter_pos[1] -= (level + 1) * 1.0
                
                inter_node = BatchNode2D(
                    pos_2D=inter_pos,
                    name=f"{layer}{group_idx + 1}_i{level}_{i // merge}",
                    layer=layer,
                )
                
                for node in group:
                    lines.append(Line2D(
                        lower_node=inter_node,
                        upper_node=node,
                        target_length=inter_length / (level + 1),  # Shorter for higher levels
                        line_type=line_type_name,
                        layer=layer,
                        name=f"{node.name}_h",
                    ))
                
                next_nodes.append(inter_node)
            
            current_nodes = next_nodes
        
        # Connect remaining to basse
        for node in current_nodes:
            lines.append(Line2D(
                lower_node=basse_node,
                upper_node=node,
                target_length=inter_length,
                line_type=line_type_name,
                layer=layer,
                name=f"{layer}{group_idx + 1}_to_basse",
            ))
        
        return lines
    
    def _calc_batch_position(self, nodes, level):
        """Calculate average 2D position for batch node."""
        positions = []
        
        for n in nodes:
            if isinstance(n, UpperNode2D):
                try:
                    cell = min(n.cell_no, self.half_cell_num - 1)
                    pos = list(self.parametric_glider.shape[cell, n.rib_pos])
                    positions.append(pos)
                except:
                    positions.append([n.cell_no * 0.5, 0])
            elif hasattr(n, 'pos_2D'):
                positions.append(list(n.pos_2D))
        
        if positions:
            return [
                sum(p[0] for p in positions) / len(positions),
                sum(p[1] for p in positions) / len(positions),
            ]
        return [0, 0]
