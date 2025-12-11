"""
Airfoil Structure Tool for OpenGlider FreeCAD workbench.

This tool allows configuration of structural elements on rib profiles:
- Rod sleeves (fourreaux de joncs) for extrados and intrados (multiple per surface)
- Attachment reinforcements with half-moon load distribution rods (suspended ribs only)
"""

from .tools import BaseTool, Line_old
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from openglider.glider.rib import RodSleeve, AttachmentReinforcement
import numpy as np
from pivy import coin
import os


class RodSleeveConfigWidget(QtGui.QWidget):
    """Widget for configuring a single rod sleeve's parameters."""
    changed = QtCore.Signal()
    
    def __init__(self, surface='extrados', parent=None):
        super(RodSleeveConfigWidget, self).__init__(parent)
        self.surface = surface
        self.layout = QtGui.QFormLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        
        # Start/End position
        self.startSpinBox = QtGui.QDoubleSpinBox()
        self.startSpinBox.setSingleStep(1.0)
        self.startSpinBox.setDecimals(1)
        self.startSpinBox.setSuffix(" %")
        self.startSpinBox.setRange(0.0, 100.0)
        self.startSpinBox.setValue(0.0)
        self.layout.addRow("Start (% chord)", self.startSpinBox)
        
        self.endSpinBox = QtGui.QDoubleSpinBox()
        self.endSpinBox.setSingleStep(1.0)
        self.endSpinBox.setDecimals(1)
        self.endSpinBox.setSuffix(" %")
        self.endSpinBox.setRange(0.0, 100.0)
        self.endSpinBox.setValue(70.0)
        self.layout.addRow("End (% chord)", self.endSpinBox)
        
        # Width and offset
        self.widthSpinBox = QtGui.QDoubleSpinBox()
        self.widthSpinBox.setSingleStep(1.0)
        self.widthSpinBox.setDecimals(1)
        self.widthSpinBox.setSuffix(" mm")
        self.widthSpinBox.setRange(1.0, 50.0)
        self.widthSpinBox.setValue(15.0)
        self.layout.addRow("Width", self.widthSpinBox)
        
        self.offsetSpinBox = QtGui.QDoubleSpinBox()
        self.offsetSpinBox.setSingleStep(0.5)
        self.offsetSpinBox.setDecimals(1)
        self.offsetSpinBox.setSuffix(" mm")
        self.offsetSpinBox.setRange(0.0, 20.0)
        self.offsetSpinBox.setValue(5.0)
        self.layout.addRow("Offset", self.offsetSpinBox)
        
        # Start termination (formerly "Leading Edge")
        self.layout.addRow(QtGui.QLabel("<b>Start Termination</b>"))
        self.startAngleSpinBox = QtGui.QDoubleSpinBox()
        self.startAngleSpinBox.setSingleStep(5.0)
        self.startAngleSpinBox.setDecimals(0)
        self.startAngleSpinBox.setSuffix(" °")
        self.startAngleSpinBox.setRange(0.0, 360.0)
        # Default angles differ by surface
        if surface == 'extrados':
            self.startAngleSpinBox.setValue(350.0)
        else:
            self.startAngleSpinBox.setValue(100.0)
        self.layout.addRow("Angle", self.startAngleSpinBox)
        
        self.startLengthSpinBox = QtGui.QDoubleSpinBox()
        self.startLengthSpinBox.setSingleStep(5.0)
        self.startLengthSpinBox.setDecimals(0)
        self.startLengthSpinBox.setSuffix(" mm")
        self.startLengthSpinBox.setRange(10.0, 200.0)
        self.startLengthSpinBox.setValue(100.0)
        self.layout.addRow("Length", self.startLengthSpinBox)
        
        # End termination (formerly "Trailing Edge")
        self.layout.addRow(QtGui.QLabel("<b>End Termination</b>"))
        self.endAngleSpinBox = QtGui.QDoubleSpinBox()
        self.endAngleSpinBox.setSingleStep(5.0)
        self.endAngleSpinBox.setDecimals(0)
        self.endAngleSpinBox.setSuffix(" °")
        self.endAngleSpinBox.setRange(0.0, 360.0)
        if surface == 'extrados':
            self.endAngleSpinBox.setValue(325.0)
        else:
            self.endAngleSpinBox.setValue(20.0)
        self.layout.addRow("Angle", self.endAngleSpinBox)
        
        self.endLengthSpinBox = QtGui.QDoubleSpinBox()
        self.endLengthSpinBox.setSingleStep(5.0)
        self.endLengthSpinBox.setDecimals(0)
        self.endLengthSpinBox.setSuffix(" mm")
        self.endLengthSpinBox.setRange(10.0, 200.0)
        self.endLengthSpinBox.setValue(75.0)
        self.layout.addRow("Length", self.endLengthSpinBox)
        
        # Excluded ribs field
        self.layout.addRow(QtGui.QLabel("<b>Exclusions</b>"))
        self.excludedRibsEdit = QtGui.QLineEdit()
        self.excludedRibsEdit.setPlaceholderText("e.g. 1, 3, 5 (rib numbers to exclude)")
        self.layout.addRow("Excluded Ribs", self.excludedRibsEdit)
        
        # Connect signals
        self.startSpinBox.valueChanged.connect(self.emit_changed)
        self.endSpinBox.valueChanged.connect(self.emit_changed)
        self.widthSpinBox.valueChanged.connect(self.emit_changed)
        self.offsetSpinBox.valueChanged.connect(self.emit_changed)
        self.startAngleSpinBox.valueChanged.connect(self.emit_changed)
        self.startLengthSpinBox.valueChanged.connect(self.emit_changed)
        self.endAngleSpinBox.valueChanged.connect(self.emit_changed)
        self.endLengthSpinBox.valueChanged.connect(self.emit_changed)
        self.excludedRibsEdit.textChanged.connect(self.emit_changed)
    
    def emit_changed(self):
        self.changed.emit()
    
    def get_excluded_ribs(self):
        """Parse excluded ribs from text field. Returns list of 0-based indices."""
        text = self.excludedRibsEdit.text().strip()
        if not text:
            return []
        try:
            # Parse comma-separated rib numbers (1-based from user, convert to 0-based)
            return [int(x.strip()) - 1 for x in text.split(',') if x.strip().isdigit()]
        except:
            return []
    
    def get_values(self):
        return {
            'start_chord': self.startSpinBox.value() / 100.0,
            'end_chord': self.endSpinBox.value() / 100.0,
            'width': self.widthSpinBox.value() / 1000.0,
            'offset': self.offsetSpinBox.value() / 1000.0,
            'start_angle': self.startAngleSpinBox.value(),
            'start_length': self.startLengthSpinBox.value() / 1000.0,
            'end_angle': self.endAngleSpinBox.value(),
            'end_length': self.endLengthSpinBox.value() / 1000.0,
            'excluded_ribs': self.get_excluded_ribs(),
        }
    
    def set_values(self, config):
        if not config:
            return
        self.startSpinBox.setValue(config.get('start_chord', 0.0) * 100.0)
        self.endSpinBox.setValue(config.get('end_chord', 0.7) * 100.0)
        self.widthSpinBox.setValue(config.get('width', 0.015) * 1000.0)
        self.offsetSpinBox.setValue(config.get('offset', 0.005) * 1000.0)
        self.startAngleSpinBox.setValue(config.get('start_angle', 350.0 if self.surface == 'extrados' else 100.0))
        self.startLengthSpinBox.setValue(config.get('start_length', 0.1) * 1000.0)
        self.endAngleSpinBox.setValue(config.get('end_angle', 325.0 if self.surface == 'extrados' else 20.0))
        self.endLengthSpinBox.setValue(config.get('end_length', 0.075) * 1000.0)
        # Load excluded ribs (convert 0-based to 1-based for display)
        excluded = config.get('excluded_ribs', [])
        if excluded:
            self.excludedRibsEdit.setText(', '.join(str(x + 1) for x in excluded))
        else:
            self.excludedRibsEdit.clear()
    
    def create_rod_sleeve(self):
        """Create a RodSleeve object from this widget's values."""
        values = self.get_values()
        return RodSleeve(
            surface=self.surface,
            width=values['width'],
            offset=values['offset'],
            start_chord=values['start_chord'],
            end_chord=values['end_chord'],
            le_angle=values['start_angle'],
            te_angle=values['end_angle'],
            le_length=values['start_length'],
            te_length=values['end_length'],
        )


class SurfaceRodSleeveGroup(QtGui.QGroupBox):
    """Group box for managing multiple rod sleeves on one surface."""
    changed = QtCore.Signal()
    
    def __init__(self, surface='extrados', title="Extrados Rod Sleeves", parent=None):
        super(SurfaceRodSleeveGroup, self).__init__(title, parent)
        self.surface = surface
        self.rod_widgets = []
        
        main_layout = QtGui.QVBoxLayout(self)
        
        # Enable checkbox
        self.enabledCheckBox = QtGui.QCheckBox("Enable")
        self.enabledCheckBox.setChecked(True)
        main_layout.addWidget(self.enabledCheckBox)
        
        # Tabs for multiple rods
        self.tabWidget = QtGui.QTabWidget()
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.tabCloseRequested.connect(self.remove_rod)
        main_layout.addWidget(self.tabWidget)
        
        # Add button
        button_layout = QtGui.QHBoxLayout()
        self.addButton = QtGui.QPushButton("+ Add Rod")
        self.addButton.clicked.connect(self.add_rod)
        button_layout.addWidget(self.addButton)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Connect enable checkbox
        self.enabledCheckBox.stateChanged.connect(self.emit_changed)
        
        # Add one rod by default
        self.add_rod()
    
    def emit_changed(self):
        self.changed.emit()
    
    def add_rod(self):
        """Add a new rod sleeve tab."""
        widget = RodSleeveConfigWidget(surface=self.surface)
        widget.changed.connect(self.emit_changed)
        
        rod_num = len(self.rod_widgets) + 1
        self.rod_widgets.append(widget)
        self.tabWidget.addTab(widget, f"Rod {rod_num}")
        self.emit_changed()
    
    def remove_rod(self, index):
        """Remove a rod sleeve tab."""
        if len(self.rod_widgets) <= 1:
            return  # Keep at least one rod
        
        widget = self.rod_widgets.pop(index)
        self.tabWidget.removeTab(index)
        widget.deleteLater()
        
        # Renumber tabs
        for i, w in enumerate(self.rod_widgets):
            self.tabWidget.setTabText(i, f"Rod {i + 1}")
        
        self.emit_changed()
    
    def is_enabled(self):
        return self.enabledCheckBox.isChecked()
    
    def get_rod_sleeves(self):
        """Get list of RodSleeve objects for all enabled rods."""
        if not self.is_enabled():
            return []
        return [w.create_rod_sleeve() for w in self.rod_widgets]
    
    def get_configs(self):
        """Get list of config dicts for all rods."""
        return [w.get_values() for w in self.rod_widgets]
    
    def set_configs(self, enabled, configs):
        """Set the widget state from a list of configs."""
        self.enabledCheckBox.setChecked(enabled)
        
        # Clear existing tabs (except first)
        while len(self.rod_widgets) > 1:
            self.remove_rod(len(self.rod_widgets) - 1)
        
        if not configs:
            return
        
        # Set first rod's values
        if len(configs) > 0 and len(self.rod_widgets) > 0:
            self.rod_widgets[0].set_values(configs[0])
        
        # Add additional rods
        for i, config in enumerate(configs[1:], start=1):
            self.add_rod()
            self.rod_widgets[i].set_values(config)


class AirfoilStructureTool(BaseTool):
    widget_name = "Airfoil Structure"

    def __init__(self, obj):
        super(AirfoilStructureTool, self).__init__(obj)

        # Profile type selector
        self.ribTypeComboBox = QtGui.QComboBox(self.base_widget)
        
        # === Extrados Sleeve Group (multiple rods) ===
        self.extradosGroup = SurfaceRodSleeveGroup(
            surface='extrados', 
            title="Extrados Rod Sleeves",
            parent=self.base_widget
        )
        
        # === Intrados Sleeve Group (multiple rods) ===
        self.intradosGroup = SurfaceRodSleeveGroup(
            surface='intrados',
            title="Intrados Rod Sleeves", 
            parent=self.base_widget
        )
        
        # === Attachment Reinforcement Group (only for suspended) ===
        self.reinforcementGroupBox = QtGui.QGroupBox("Attachment Reinforcements", self.base_widget)
        self.reinforcementLayout = QtGui.QFormLayout(self.reinforcementGroupBox)
        
        self.reinforcementEnabledCheckBox = QtGui.QCheckBox("Enable Reinforcements", self.reinforcementGroupBox)
        self.reinforcementEnabledCheckBox.setChecked(True)  # Enabled by default
        self.reinforcementApplyAllCheckBox = QtGui.QCheckBox("Apply same parameters to all", self.reinforcementGroupBox)
        self.reinforcementApplyAllCheckBox.setChecked(False)  # Individual config by default
        
        self.reinforcementStack = QtGui.QStackedWidget(self.reinforcementGroupBox)
        
        # Master Config
        self.masterConfig = ReinforcementConfigWidget(self.reinforcementGroupBox)
        self.reinforcementStack.addWidget(self.masterConfig)
        
        # Tabbed Config
        self.reinforcementTabs = QtGui.QTabWidget(self.reinforcementGroupBox)
        self.reinforcementStack.addWidget(self.reinforcementTabs)
        self.reinforcement_widgets = []

        self.applyButton = QtGui.QPushButton("Apply", self.base_widget)

        # Preview rib selector
        self.previewRibLabel = QtGui.QLabel("Preview Rib:")
        self.previewRibSpinBox = QtGui.QSpinBox(self.base_widget)
        self.previewRibSpinBox.setRange(0, self.get_num_ribs() - 1)
        self.previewRibSpinBox.setValue(0)

        self.preview_root = coin.SoSeparator()
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        self.ribTypeComboBox.addItems(["Non-Suspended", "Suspended"])
        self.layout.addRow("Profile Type", self.ribTypeComboBox)
        
        # Add rod sleeve groups
        self.layout.addRow(self.extradosGroup)
        self.layout.addRow(self.intradosGroup)
        
        # --- Configure Attachment Reinforcements ---
        self.reinforcementLayout.addRow(self.reinforcementEnabledCheckBox)
        self.reinforcementLayout.addRow(self.reinforcementApplyAllCheckBox)
        self.reinforcementLayout.addRow(self.reinforcementStack)
        
        self.layout.addRow(self.reinforcementGroupBox)
        
        # Preview selector
        preview_layout = QtGui.QHBoxLayout()
        preview_layout.addWidget(self.previewRibLabel)
        preview_layout.addWidget(self.previewRibSpinBox)
        preview_layout.addStretch()
        self.layout.addRow(preview_layout)
        
        # Apply button
        button_layout = QtGui.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.applyButton)
        self.layout.addRow(button_layout)

        # Load initial values
        self.update_form_from_glider_data()

        # Connections - Rod sleeves
        self.extradosGroup.changed.connect(self.update_preview)
        self.intradosGroup.changed.connect(self.update_preview)
        
        # Connections - Reinforcements
        self.reinforcementEnabledCheckBox.stateChanged.connect(self.update_preview)
        self.reinforcementApplyAllCheckBox.stateChanged.connect(self.on_reinforcement_mode_change)
        self.reinforcementApplyAllCheckBox.stateChanged.connect(self.update_preview)
        # Master config signals are connected in ReinforcementConfigWidget
        self.masterConfig.changed.connect(self.update_preview)
        
        self.ribTypeComboBox.currentIndexChanged.connect(self.on_rib_type_change)
        self.previewRibSpinBox.valueChanged.connect(self.update_preview)
        self.applyButton.clicked.connect(self.accept)

        # Set initial visibility of reinforcement group (only for suspended)
        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        self.reinforcementGroupBox.setVisible(is_suspended)
        
        # Always initialize reinforcement tabs (even if Non-Suspended is selected)
        # so they're ready when switching to Suspended
        rib = self.get_first_suspended_rib()
        if rib:
            valid_aps = self.get_valid_attachment_points(rib)
            self.update_reinforcement_tabs(valid_aps)
        
        # Ensure correct stack widget is shown
        self.on_reinforcement_mode_change(None)

    def setup_pivy(self):
        self.task_separator.addChild(self.preview_root)
        self.update_preview()
        Gui.SendMsgToActiveView("ViewFit")

    def get_num_ribs(self):
        """Get total number of ribs."""
        try:
            glider_instance = self.obj.Proxy.getGliderInstance()
            return len(glider_instance.ribs)
        except:
            return 1

    def get_representative_rib(self, suspended=False):
        """Get rib for preview based on spinner selection."""
        glider_instance = self.obj.Proxy.getGliderInstance()
        rib_idx = self.previewRibSpinBox.value()
        
        if rib_idx < len(glider_instance.ribs):
            return glider_instance.ribs[rib_idx]
        return glider_instance.ribs[0] if glider_instance.ribs else None

    def get_first_suspended_rib(self):
        """Get the first suspended rib that has valid attachment points (< 90% chord)."""
        glider_instance = self.obj.Proxy.getGliderInstance()
        suspended_ribs = {att.rib for att in glider_instance.attachment_points if hasattr(att, 'rib')}
        
        for rib in glider_instance.ribs:
            if rib in suspended_ribs:
                # Check if this rib has valid attachment points (< 90%)
                all_aps = glider_instance.get_rib_attachment_points(rib)
                valid_aps = [ap for ap in all_aps if ap.rib_pos <= 0.90]
                if valid_aps:
                    return rib
        
        return glider_instance.ribs[0] if glider_instance.ribs else None
    
    def get_valid_attachment_points(self, rib):
        """Get attachment points < 90% chord (excluding brake attachments)."""
        glider_instance = self.obj.Proxy.getGliderInstance()
        all_aps = glider_instance.get_rib_attachment_points(rib)
        # Filter out brake attachments (> 90% chord)
        valid_aps = [ap for ap in all_aps if ap.rib_pos <= 0.90]
        # Sort by position
        valid_aps.sort(key=lambda x: x.rib_pos)
        return valid_aps

    def get_first_suspended_rib_index(self):
        """Get the index of the first suspended rib with valid attachment points."""
        glider_instance = self.obj.Proxy.getGliderInstance()
        suspended_ribs = {att.rib for att in glider_instance.attachment_points if hasattr(att, 'rib')}
        
        for idx, rib in enumerate(glider_instance.ribs):
            if rib in suspended_ribs:
                # Check if this rib has valid attachment points (< 90%)
                all_aps = glider_instance.get_rib_attachment_points(rib)
                valid_aps = [ap for ap in all_aps if ap.rib_pos <= 0.90]
                if valid_aps:
                    return idx
        return 0

    def on_rib_type_change(self, new_index):
        previous_index = 1 - new_index
        # Save data for previous state
        self.update_glider_data(is_suspended=previous_index == 1)
        
        is_suspended = new_index == 1
        self.reinforcementGroupBox.setVisible(is_suspended)
        
        # Auto-switch preview rib to first suspended rib when switching to Suspended mode
        if is_suspended:
            first_suspended_idx = self.get_first_suspended_rib_index()
            self.previewRibSpinBox.setValue(first_suspended_idx)
        
        # Reload data for new state
        self.update_form_from_glider_data()
        self.update_preview(force=True)

    def on_reinforcement_mode_change(self, state):
        """Switch between Master and Tabbed view."""
        if self.reinforcementApplyAllCheckBox.isChecked():
            self.reinforcementStack.setCurrentWidget(self.masterConfig)
        else:
            self.reinforcementStack.setCurrentWidget(self.reinforcementTabs)

    def update_reinforcement_tabs(self, valid_aps):
        """Rebuild tabs based on current valid attachment points."""
        self.reinforcementTabs.clear()
        self.reinforcement_widgets = []
        
        for i, ap in enumerate(valid_aps):
            label = "AP {} ({:.1f}%)".format(i + 1, ap.rib_pos * 100)
            widget = ReinforcementConfigWidget()
            widget.changed.connect(self.update_preview)
            self.reinforcementTabs.addTab(widget, label)
            self.reinforcement_widgets.append(widget)

    def update_preview(self, *args, **kwargs):
        self.preview_root.removeAllChildren()

        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        rib = self.get_representative_rib(suspended=is_suspended)
        if not rib:
            return

        # Draw profile outline - scaled by chord
        profile_points = [p * rib.chord for p in rib.profile_2d.data]
        profile_3d = [[p[0], p[1], 0] for p in profile_points]
        self.preview_root.addChild(Line_old(profile_3d + [profile_3d[0]], width=2).object)
        
        # Visualizing attachment points (red dots) if suspended
        valid_aps = []
        if is_suspended:
            valid_aps = self.get_valid_attachment_points(rib)
            for ap in valid_aps:
                self._draw_attachment_point_marker(rib, ap.rib_pos)

        # Draw extrados sleeves
        for sleeve in self.extradosGroup.get_rod_sleeves():
            self._draw_sleeve(sleeve, rib, color='blue')

        # Draw intrados sleeves
        for sleeve in self.intradosGroup.get_rod_sleeves():
            self._draw_sleeve(sleeve, rib, color='green')

        # Draw attachment reinforcements if enabled and suspended
        if is_suspended and self.reinforcementEnabledCheckBox.isChecked():
            apply_all = self.reinforcementApplyAllCheckBox.isChecked()
            
            for i, ap in enumerate(valid_aps):
                # Get config
                if apply_all:
                    config = self.masterConfig.get_values()
                else:
                    # Individual config
                    if i < len(self.reinforcement_widgets):
                        config = self.reinforcement_widgets[i].get_values()
                    else:
                        continue # Should not happen if tabs aligned with valid_aps
                
                if config['enabled']:
                    reinforcement = self._create_reinforcement(ap.rib_pos, config)
                    self._draw_reinforcement(reinforcement, rib)

    def _create_reinforcement(self, position, config, name=""):
        """Create an AttachmentReinforcement from config values."""
        return AttachmentReinforcement(
            position=position,
            surface_offset=config.get('surface_offset', 0.003),
            halfmoon_radius=config['halfmoon_radius'],
            rod_enabled=config.get('rod_enabled', True),
            rod_offset=config['rod_offset'],
            rod_width=config['rod_width'],
            rod_end_offset=config.get('rod_end_offset', 10.0),
            name=name,
        )


    def _draw_sleeve(self, sleeve, rib, color='blue'):
        """Draw a rod sleeve preview with terminations."""
        try:
            # Get full sleeve with terminations
            inner_points, outer_points = sleeve.get_full_sleeve_points(rib)
            
            if inner_points and outer_points:
                # Draw inner edge
                inner_3d = [[p[0], p[1], 0] for p in inner_points]
                self.preview_root.addChild(Line_old(inner_3d, color=color, width=2).object)
                
                # Draw outer edge
                outer_3d = [[p[0], p[1], 0] for p in outer_points]
                self.preview_root.addChild(Line_old(outer_3d, color=color, width=2).object)
                
                # Draw end caps connecting inner and outer
                if len(inner_points) > 0 and len(outer_points) > 0:
                    # Start cap
                    start_cap = [[inner_points[0][0], inner_points[0][1], 0],
                                 [outer_points[0][0], outer_points[0][1], 0]]
                    self.preview_root.addChild(Line_old(start_cap, color=color, width=1).object)
                    
                    # End cap
                    end_cap = [[inner_points[-1][0], inner_points[-1][1], 0],
                               [outer_points[-1][0], outer_points[-1][1], 0]]
                    self.preview_root.addChild(Line_old(end_cap, color=color, width=1).object)
        except Exception as e:
            print(f"Error drawing sleeve: {e}")

    def _draw_attachment_point_marker(self, rib, position):
        """Draw a red marker at the attachment point position."""
        profile = rib.profile_2d
        # Get point from profile coordinate system
        idx = profile(position)
        center_point = profile[idx] * rib.chord
        
        # Create a small diamond marker
        size = 0.005  # 5mm visual size
        center_3d = np.array([center_point[0], center_point[1], 0])
        
        marker_points = [
            center_3d + np.array([size, 0, 0]),
            center_3d + np.array([0, size, 0]),
            center_3d + np.array([-size, 0, 0]),
            center_3d + np.array([0, -size, 0]),
            center_3d + np.array([size, 0, 0])
        ]
        
        self.preview_root.addChild(Line_old(marker_points, color='red', width=3).object)

    def _draw_reinforcement(self, reinforcement, rib):
        """Draw an attachment reinforcement preview."""
        try:
            flat = reinforcement.get_flattened(rib)
            
            # Draw half-moon fabric reinforcement in yellow
            halfmoon_points = [[p[0], p[1], 0] for p in flat['halfmoon'].data]
            if halfmoon_points:
                self.preview_root.addChild(Line_old(halfmoon_points, color='yellow', width=2).object)
            
            # Draw rod sleeve in red
            rod_points = [[p[0], p[1], 0] for p in flat['rod_sleeve'].data]
            if rod_points:
                self.preview_root.addChild(Line_old(rod_points, color='red', width=2).object)
        except Exception as e:
            print(f"Error drawing reinforcement: {e}")

    def update_form_from_glider_data(self):
        """Load values from parametric glider into UI."""
        pg = self.parametric_glider
        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        suffix = "_s" if is_suspended else "_ns"

        # Load extrados rod sleeve configs (new multi-rod format)
        extrados_enabled = getattr(pg, f'extrados_sleeves_enabled{suffix}', True)
        extrados_configs = getattr(pg, f'extrados_sleeves{suffix}', None)
        
        # Backward compatibility: migrate old single-rod format
        if extrados_configs is None:
            old_enabled = getattr(pg, f'extrados_sleeve_enabled{suffix}', True)
            old_config = {
                'start_chord': getattr(pg, f'extrados_sleeve_start{suffix}', 0.0),
                'end_chord': getattr(pg, f'extrados_sleeve_end{suffix}', 0.71),
                'width': getattr(pg, f'extrados_sleeve_width{suffix}', 0.015),
                'offset': getattr(pg, f'extrados_sleeve_offset{suffix}', 0.005),
                'start_angle': getattr(pg, f'extrados_sleeve_le_angle{suffix}', 350.0),
                'start_length': getattr(pg, f'extrados_sleeve_le_length{suffix}', 0.125),
                'end_angle': getattr(pg, f'extrados_sleeve_te_angle{suffix}', 325.0),
                'end_length': getattr(pg, f'extrados_sleeve_te_length{suffix}', 0.075),
            }
            extrados_configs = [old_config]
            extrados_enabled = old_enabled
        
        self.extradosGroup.set_configs(extrados_enabled, extrados_configs)

        # Load intrados rod sleeve configs (new multi-rod format)
        intrados_enabled = getattr(pg, f'intrados_sleeves_enabled{suffix}', True)
        intrados_configs = getattr(pg, f'intrados_sleeves{suffix}', None)
        
        # Backward compatibility: migrate old single-rod format
        if intrados_configs is None:
            old_enabled = getattr(pg, f'intrados_sleeve_enabled{suffix}', True)
            old_config = {
                'start_chord': getattr(pg, f'intrados_sleeve_start{suffix}', 0.06),
                'end_chord': getattr(pg, f'intrados_sleeve_end{suffix}', 0.50),
                'width': getattr(pg, f'intrados_sleeve_width{suffix}', 0.015),
                'offset': getattr(pg, f'intrados_sleeve_offset{suffix}', 0.005),
                'start_angle': getattr(pg, f'intrados_sleeve_le_angle{suffix}', 100.0),
                'start_length': getattr(pg, f'intrados_sleeve_le_length{suffix}', 0.100),
                'end_angle': getattr(pg, f'intrados_sleeve_te_angle{suffix}', 20.0),
                'end_length': getattr(pg, f'intrados_sleeve_te_length{suffix}', 0.090),
            }
            intrados_configs = [old_config]
            intrados_enabled = old_enabled
            
        self.intradosGroup.set_configs(intrados_enabled, intrados_configs)

        # Load reinforcement values (only for suspended)
        if is_suspended:
            # Rebuild tabs first - use first suspended rib to get attachment points
            rib = self.get_first_suspended_rib()
            if rib:
                valid_aps = self.get_valid_attachment_points(rib)
                self.update_reinforcement_tabs(valid_aps)
            
            # Global Enable/ApplyAll
            self.reinforcementEnabledCheckBox.setChecked(getattr(pg, 'reinforcement_enabled_s', True))
            apply_all = getattr(pg, 'reinforcement_apply_all_s', False)
            self.reinforcementApplyAllCheckBox.setChecked(apply_all)
            self.on_reinforcement_mode_change(None) # Update stack

            # Load Master Config
            master_config = getattr(pg, 'reinforcement_master_s', {})
            self.masterConfig.set_values(master_config)
            
            # Load Individual Configs
            configs = getattr(pg, 'reinforcement_configs_s', [])
            for i, widget in enumerate(self.reinforcement_widgets):
                if i < len(configs):
                    widget.set_values(configs[i])
                else:
                    pass

    def update_glider_data(self, is_suspended):
        """Save UI values to parametric glider."""
        pg = self.parametric_glider
        suffix = "_s" if is_suspended else "_ns"

        # Save extrados rod sleeve configs (new multi-rod format)
        setattr(pg, f'extrados_sleeves_enabled{suffix}', self.extradosGroup.is_enabled())
        setattr(pg, f'extrados_sleeves{suffix}', self.extradosGroup.get_configs())

        # Save intrados rod sleeve configs (new multi-rod format)
        setattr(pg, f'intrados_sleeves_enabled{suffix}', self.intradosGroup.is_enabled())
        setattr(pg, f'intrados_sleeves{suffix}', self.intradosGroup.get_configs())

        # Save reinforcement values (only for suspended)
        if is_suspended:
            setattr(pg, 'reinforcement_enabled_s', self.reinforcementEnabledCheckBox.isChecked())
            setattr(pg, 'reinforcement_apply_all_s', self.reinforcementApplyAllCheckBox.isChecked())
            setattr(pg, 'reinforcement_master_s', self.masterConfig.get_values())
            
            # Save list of configs
            configs = [w.get_values() for w in self.reinforcement_widgets]
            setattr(pg, 'reinforcement_configs_s', configs)

    def apply_reinforcements_to_ribs(self):
        """Apply reinforcement configurations to the actual rib objects for 2D export."""
        pg = self.parametric_glider
        glider_instance = self.obj.Proxy.getGliderInstance()
        
        # Only apply if reinforcements are enabled for suspended ribs
        if not getattr(pg, 'reinforcement_enabled_s', False):
            # Clear reinforcements from all ribs
            for rib in glider_instance.ribs:
                rib.reinforcements = []
            return
        
        apply_all = getattr(pg, 'reinforcement_apply_all_s', False)
        master_config = getattr(pg, 'reinforcement_master_s', {})
        configs = getattr(pg, 'reinforcement_configs_s', [])
        
        # Identify suspended ribs and build rib index map
        suspended_ribs = {att.rib for att in glider_instance.attachment_points if hasattr(att, 'rib')}
        
        for rib_idx, rib in enumerate(glider_instance.ribs):
            if rib in suspended_ribs:
                # Get valid attachment points for this rib
                valid_aps = self.get_valid_attachment_points(rib)
                
                reinforcements = []
                for i, ap in enumerate(valid_aps):
                    # Get config
                    if apply_all:
                        config = master_config
                    else:
                        config = configs[i] if i < len(configs) else master_config
                    
                    if config.get('enabled', True):
                        # Generate name: rib index + attachment point name (contains line letter)
                        # ap.name typically contains the line letter (A, B, C, D, etc.)
                        name = f"{rib_idx + 1}{ap.name}" if ap.name else f"{rib_idx + 1}_{i + 1}"
                        
                        reinforcement = self._create_reinforcement(ap.rib_pos, config, name)
                        reinforcements.append(reinforcement)
                
                rib.reinforcements = reinforcements
            else:
                # Non-suspended ribs don't get reinforcements
                rib.reinforcements = []

    def apply_rod_sleeves_to_ribs(self):
        """Apply rod sleeve configurations to the actual rib objects for 2D export."""
        from openglider.glider.rib.elements import RodSleeve
        
        pg = self.parametric_glider
        glider_instance = self.obj.Proxy.getGliderInstance()
        
        # Identify suspended ribs
        suspended_ribs = {att.rib for att in glider_instance.lineset.attachment_points if hasattr(att, 'rib')}
        
        for rib_idx, rib in enumerate(glider_instance.ribs):
            is_suspended = rib in suspended_ribs
            suffix = '_s' if is_suspended else '_ns'
            
            rod_sleeves = []
            
            # Get extrados sleeves
            extrados_enabled = getattr(pg, f'extrados_sleeves_enabled{suffix}', True)
            extrados_configs = getattr(pg, f'extrados_sleeves{suffix}', [])
            
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
            intrados_enabled = getattr(pg, f'intrados_sleeves_enabled{suffix}', True)
            intrados_configs = getattr(pg, f'intrados_sleeves{suffix}', [])
            
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

    def accept(self):
        is_suspended = self.ribTypeComboBox.currentIndex() == 1
        self.update_glider_data(is_suspended)
        # Apply reinforcements and rod sleeves to ribs for 2D export
        self.apply_reinforcements_to_ribs()
        self.apply_rod_sleeves_to_ribs()
        self.update_view_glider()
        super(AirfoilStructureTool, self).accept()


class ReinforcementConfigWidget(QtGui.QWidget):
    """Widget for configuring a single reinforcement's parameters."""
    changed = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(ReinforcementConfigWidget, self).__init__(parent)
        self.layout = QtGui.QFormLayout(self)
        self.layout.setContentsMargins(0, 5, 0, 5)
        
        self.enableCheckBox = QtGui.QCheckBox("Enable")
        self.enableCheckBox.setChecked(True)
        self.layout.addRow(self.enableCheckBox)
        
        self.surfaceOffsetSpinBox = QtGui.QDoubleSpinBox()
        self.surfaceOffsetSpinBox.setSingleStep(0.5)
        self.surfaceOffsetSpinBox.setDecimals(1)
        self.surfaceOffsetSpinBox.setSuffix(" mm")
        self.surfaceOffsetSpinBox.setRange(0.0, 1000.0)
        self.surfaceOffsetSpinBox.setValue(0.5)  # 0.5mm default
        self.layout.addRow("Surface offset", self.surfaceOffsetSpinBox)
        
        self.halfmoonRadiusSpinBox = QtGui.QDoubleSpinBox()
        self.halfmoonRadiusSpinBox.setSingleStep(1.0)
        self.halfmoonRadiusSpinBox.setDecimals(1)
        self.halfmoonRadiusSpinBox.setSuffix(" mm")
        self.halfmoonRadiusSpinBox.setRange(0.0, 1000.0)
        self.halfmoonRadiusSpinBox.setValue(100.0)  # 100mm default
        self.layout.addRow("Half-moon radius", self.halfmoonRadiusSpinBox)
        
        self.rodEnabledCheckBox = QtGui.QCheckBox("Enable Rod Sleeve")
        self.rodEnabledCheckBox.setChecked(True)
        self.layout.addRow(self.rodEnabledCheckBox)
        
        self.rodOffsetSpinBox = QtGui.QDoubleSpinBox()
        self.rodOffsetSpinBox.setSingleStep(1.0)
        self.rodOffsetSpinBox.setDecimals(1)
        self.rodOffsetSpinBox.setSuffix(" mm")
        self.rodOffsetSpinBox.setRange(0.0, 1000.0)
        self.rodOffsetSpinBox.setValue(8.0)  # 8mm default
        self.layout.addRow("Rod offset", self.rodOffsetSpinBox)
        
        self.rodWidthSpinBox = QtGui.QDoubleSpinBox()
        self.rodWidthSpinBox.setSingleStep(0.5)
        self.rodWidthSpinBox.setDecimals(1)
        self.rodWidthSpinBox.setSuffix(" mm")
        self.rodWidthSpinBox.setRange(0.0, 1000.0)
        self.rodWidthSpinBox.setValue(9.0)  # 9mm default
        self.layout.addRow("Rod width", self.rodWidthSpinBox)
        
        self.rodEndOffsetSpinBox = QtGui.QDoubleSpinBox()
        self.rodEndOffsetSpinBox.setSingleStep(1.0)
        self.rodEndOffsetSpinBox.setDecimals(1)
        self.rodEndOffsetSpinBox.setSuffix(" °")
        self.rodEndOffsetSpinBox.setRange(0.0, 90.0)
        self.rodEndOffsetSpinBox.setValue(1.0)  # 1° default
        self.layout.addRow("Rod end offset", self.rodEndOffsetSpinBox)
        
        self.enableCheckBox.stateChanged.connect(self.emit_changed)
        self.surfaceOffsetSpinBox.valueChanged.connect(self.emit_changed)
        self.halfmoonRadiusSpinBox.valueChanged.connect(self.emit_changed)
        self.rodEnabledCheckBox.stateChanged.connect(self.emit_changed)
        self.rodOffsetSpinBox.valueChanged.connect(self.emit_changed)
        self.rodWidthSpinBox.valueChanged.connect(self.emit_changed)
        self.rodEndOffsetSpinBox.valueChanged.connect(self.emit_changed)
        
    def emit_changed(self):
        self.changed.emit()
        
    def get_values(self):
        return {
            'enabled': self.enableCheckBox.isChecked(),
            'surface_offset': self.surfaceOffsetSpinBox.value() / 1000.0,
            'halfmoon_radius': self.halfmoonRadiusSpinBox.value() / 1000.0,
            'rod_enabled': self.rodEnabledCheckBox.isChecked(),
            'rod_offset': self.rodOffsetSpinBox.value() / 1000.0,
            'rod_width': self.rodWidthSpinBox.value() / 1000.0,
            'rod_end_offset': self.rodEndOffsetSpinBox.value(),
        }
        
    def set_values(self, config):
        if not config:
            return
        self.enableCheckBox.setChecked(config.get('enabled', True))
        self.surfaceOffsetSpinBox.setValue(config.get('surface_offset', 0.003) * 1000.0)
        self.halfmoonRadiusSpinBox.setValue(config.get('halfmoon_radius', 0.03) * 1000.0)
        self.rodEnabledCheckBox.setChecked(config.get('rod_enabled', True))
        self.rodOffsetSpinBox.setValue(config.get('rod_offset', 0.005) * 1000.0)
        self.rodWidthSpinBox.setValue(config.get('rod_width', 0.005) * 1000.0)
        self.rodEndOffsetSpinBox.setValue(config.get('rod_end_offset', 10.0))

