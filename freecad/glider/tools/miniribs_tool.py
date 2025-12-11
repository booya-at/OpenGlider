from .tools import BaseTool, input_field, Line_old
from .table import base_table_widget
from .glider import draw_glider
from PySide import QtGui
from openglider.glider.rib import MiniRib
from pivy import coin
import FreeCADGui as Gui
import numpy as np


class MiniRibsTool(BaseTool):
    hide = True
    turn = False
    widget_name = "Mini Ribs"

    def __init__(self, obj):
        super(MiniRibsTool, self).__init__(obj)
        self.miniribs_table = miniribs_table()
        self.miniribs_table.get_from_ParametricGlider(self.parametric_glider)
        
        # If no miniribs in elements, populate with defaults
        if not self.parametric_glider.elements.get("miniribs"):
            self.set_defaults()
            # Apply defaults immediately so they exist in backend
            self.apply_elements()

        self.miniribs_button = QtGui.QPushButton("edit miniribs")
        self.miniribs_button.clicked.connect(self.miniribs_table.show)
        self.layout.setWidget(0, input_field, self.miniribs_button)

        # Minirib hole settings section
        self.layout.addRow(QtGui.QLabel("<b>Minirib Hole Settings</b>"))
        
        self.holesCheckBox = QtGui.QCheckBox("Enable Holes")
        self.holesCheckBox.setChecked(getattr(self.parametric_glider, 'minirib_holes', False))
        self.holesCheckBox.stateChanged.connect(self.on_hole_settings_changed)
        self.layout.addRow(QtGui.QLabel(""), self.holesCheckBox)

        self.numHolesSpinBox = QtGui.QSpinBox()
        self.numHolesSpinBox.setRange(1, 30)
        self.numHolesSpinBox.setValue(getattr(self.parametric_glider, 'minirib_num_holes', 1))
        self.numHolesSpinBox.valueChanged.connect(self.on_hole_settings_changed)
        self.layout.addRow(QtGui.QLabel("Number of Holes:"), self.numHolesSpinBox)

        self.holeWidthSpinBox = QtGui.QDoubleSpinBox()
        self.holeWidthSpinBox.setRange(0.1, 0.9)
        self.holeWidthSpinBox.setSingleStep(0.05)
        self.holeWidthSpinBox.setDecimals(2)
        self.holeWidthSpinBox.setValue(getattr(self.parametric_glider, 'minirib_hole_width', 0.5))
        self.holeWidthSpinBox.valueChanged.connect(self.on_hole_settings_changed)
        self.layout.addRow(QtGui.QLabel("Hole Width (%):"), self.holeWidthSpinBox)

        self.holeHeightSpinBox = QtGui.QDoubleSpinBox()
        self.holeHeightSpinBox.setRange(0.1, 0.9)
        self.holeHeightSpinBox.setSingleStep(0.05)
        self.holeHeightSpinBox.setDecimals(2)
        self.holeHeightSpinBox.setValue(getattr(self.parametric_glider, 'minirib_hole_height', 0.7))
        self.holeHeightSpinBox.valueChanged.connect(self.on_hole_settings_changed)
        self.layout.addRow(QtGui.QLabel("Hole Height (%):"), self.holeHeightSpinBox)

        self.holeShapeComboBox = QtGui.QComboBox()
        self.holeShapeComboBox.addItems(["Ellipse", "Rounded Rectangle"])
        self.holeShapeComboBox.setCurrentIndex(getattr(self.parametric_glider, 'minirib_hole_shape', 0))
        self.holeShapeComboBox.currentIndexChanged.connect(self.on_hole_settings_changed)
        self.layout.addRow(QtGui.QLabel("Hole Shape:"), self.holeShapeComboBox)

        self.maxPosSpinBox = QtGui.QDoubleSpinBox()
        self.maxPosSpinBox.setRange(0.5, 1.0)
        self.maxPosSpinBox.setSingleStep(0.05)
        self.maxPosSpinBox.setDecimals(2)
        self.maxPosSpinBox.setValue(getattr(self.parametric_glider, 'minirib_hole_max_pos', 0.9))
        self.maxPosSpinBox.valueChanged.connect(self.on_hole_settings_changed)
        self.layout.addRow(QtGui.QLabel("Max Position (%):"), self.maxPosSpinBox)

        # Cell selector for 2D preview
        self.layout.addRow(QtGui.QLabel("<b>2D Preview</b>"))
        self.cellSpinBox = QtGui.QSpinBox()
        self.cellSpinBox.setRange(0, max(0, self.get_num_cells() - 1))
        self.cellSpinBox.setValue(0)
        self.cellSpinBox.valueChanged.connect(self.update_preview)
        self.layout.addRow(QtGui.QLabel("Preview Cell:"), self.cellSpinBox)

        # 2D Preview area
        self.preview_root = coin.SoSeparator()
        self.task_separator.addChild(self.preview_root)
        
        self.draw_glider()
        self.update_preview()
        Gui.SendMsgToActiveView("ViewFit")

    def get_num_cells(self):
        try:
            glider_inst = self.obj.Proxy.getGliderInstance()
            return len(glider_inst.cells)
        except:
            return 1

    def on_hole_settings_changed(self, *args):
        """Update parametric glider with new hole settings."""
        self.parametric_glider.minirib_holes = self.holesCheckBox.isChecked()
        self.parametric_glider.minirib_num_holes = self.numHolesSpinBox.value()
        self.parametric_glider.minirib_hole_width = self.holeWidthSpinBox.value()
        self.parametric_glider.minirib_hole_height = self.holeHeightSpinBox.value()
        self.parametric_glider.minirib_hole_shape = self.holeShapeComboBox.currentIndex()
        self.parametric_glider.minirib_hole_max_pos = self.maxPosSpinBox.value()
        self.update_preview()

    def set_defaults(self):
        try:
            glider_inst = self.obj.Proxy.getGliderInstance()
            num_cells = len(glider_inst.cells)
            all_cells = list(range(num_cells))
        except Exception:
            all_cells = [0] 

        default_row = {
            "yvalue": 0.5,
            "intrados_start": 0.8,
            "extrados_start": 0.75,
            "end_distance_cm": 2.0,
            "transition_length": 0.05,
            "cells": all_cells
        }
        
        self.miniribs_table.table.setRowCount(1)
        self.miniribs_table.set_row(0, default_row)

    def draw_glider(self):
        # Don't remove all children - the preview_root is also a child
        pass  # We'll only use 2D preview now

    def update_preview(self):
        """Draw 2D preview of a representative minirib with holes."""
        self.preview_root.removeAllChildren()
        
        try:
            glider_inst = self.parametric_glider.get_glider_3d()
            cell_idx = self.cellSpinBox.value()
            
            if cell_idx >= len(glider_inst.cells):
                return
            
            cell = glider_inst.cells[cell_idx]
            
            # Check if this cell has miniribs
            if not cell.miniribs:
                # Create a temporary minirib for preview
                minirib_data = self.get_first_minirib_data()
                if minirib_data is None:
                    return
                    
                # Apply hole settings
                if self.holesCheckBox.isChecked():
                    minirib_data['num_holes'] = self.numHolesSpinBox.value()
                    minirib_data['hole_width'] = self.holeWidthSpinBox.value()
                    minirib_data['hole_height'] = self.holeHeightSpinBox.value()
                    minirib_data['hole_shape'] = self.holeShapeComboBox.currentIndex()
                    minirib_data['hole_max_pos'] = self.maxPosSpinBox.value()
                else:
                    minirib_data['num_holes'] = 0
                
                minirib = MiniRib(**minirib_data)
            else:
                # Use the first minirib in the cell
                minirib = cell.miniribs[0]
                # Update hole settings for preview
                if self.holesCheckBox.isChecked():
                    minirib.num_holes = self.numHolesSpinBox.value()
                    minirib.hole_width = self.holeWidthSpinBox.value()
                    minirib.hole_height = self.holeHeightSpinBox.value()
                    minirib.hole_shape = self.holeShapeComboBox.currentIndex()
                    minirib.hole_max_pos = self.maxPosSpinBox.value()
                else:
                    minirib.num_holes = 0

            # Get the 2D shape
            shape_2d = minirib.get_2d_shape(cell)
            if shape_2d is None or len(shape_2d.data) < 3:
                return
            
            # Draw the minirib contour
            contour_pts = list(shape_2d.data) + [shape_2d.data[0]]  # Close the loop
            self.preview_root.addChild(Line_old(contour_pts, color='green', width=2).object)
            
            # Draw holes if enabled
            if minirib.num_holes > 0:
                holes = minirib.generate_holes(cell)
                for hole_pts, hole_center in holes:
                    if len(hole_pts) >= 3:
                        hole_contour = list(hole_pts)
                        # Close the hole contour if not already closed
                        if not np.allclose(hole_contour[0], hole_contour[-1]):
                            hole_contour.append(hole_contour[0])
                        self.preview_root.addChild(Line_old(hole_contour, color='blue', width=2).object)
                        
                        # Draw center marker
                        marker = coin.SoSeparator()
                        trans = coin.SoTranslation()
                        trans.translation = (hole_center[0], hole_center[1], 0)
                        mat = coin.SoMaterial()
                        mat.diffuseColor.setValue(0, 0, 1)  # Blue
                        sphere = coin.SoSphere()
                        sphere.radius = 0.002
                        marker.addChild(trans)
                        marker.addChild(mat)
                        marker.addChild(sphere)
                        self.preview_root.addChild(marker)

        except Exception as e:
            print(f"Error updating minirib preview: {e}")

    def get_first_minirib_data(self):
        """Get data for the first minirib from the table."""
        miniribs = self.parametric_glider.elements.get("miniribs", [])
        if miniribs:
            data = miniribs[0].copy()
            data.pop("cells", None)
            return data
        return {
            "yvalue": 0.5,
            "intrados_start": 0.8,
            "extrados_start": 0.75,
            "end_distance": 0.02,
            "transition_length": 0.05,
        }

    def apply_elements(self):
        self.miniribs_table.apply_to_glider(self.parametric_glider)
        # Only update preview if preview_root exists (may be called during init)
        if hasattr(self, 'preview_root'):
            self.update_preview()

    def accept(self):
        self.apply_elements()
        self.update_view_glider()
        self.miniribs_table.hide()
        del self.miniribs_table
        self.task_separator.removeAllChildren()
        super(MiniRibsTool, self).accept()

    def reject(self):
        self.miniribs_table.hide()
        del self.miniribs_table
        self.task_separator.removeAllChildren()
        super(MiniRibsTool, self).reject()


class miniribs_table(base_table_widget):
    name = "miniribs"
    keyword = "miniribs"

    def __init__(self):
        super(miniribs_table, self).__init__(name="miniribs")
        self.table.setRowCount(200)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "y_value",
                "int_start",
                "ext_start",
                "end_cm",
                "trans_len",
                "cells",
            ]
        )

    def get_from_ParametricGlider(self, ParametricGlider):
        if "miniribs" in ParametricGlider.elements:
            miniribs = ParametricGlider.elements["miniribs"]
            for row, element in enumerate(miniribs):
                end_dist_cm = (element.get("end_distance") or 0.02) * 100
                entries = [
                    element.get("yvalue", 0.5),
                    element.get("intrados_start", 0.8),
                    element.get("extrados_start", 0.75),
                    end_dist_cm,
                    element.get("transition_length", 0.05),
                ]
                entries.append(element.get("cells", [0]))
                self.table.setRow(row, entries)

    def set_row(self, row_idx, data):
        entries = [
            data["yvalue"],
            data["intrados_start"],
            data["extrados_start"],
            data.get("end_distance_cm", 2.0),
            data.get("transition_length", 0.05),
            data["cells"]
        ]
        self.table.setRow(row_idx, entries)

    def apply_to_glider(self, ParametricGlider):
        num_rows = self.table.rowCount()
        ParametricGlider.elements[self.keyword] = []
        for n_row in range(num_rows):
            row = self.get_row(n_row)
            if row:
                minirib = {}
                minirib["yvalue"] = row[0]
                minirib["intrados_start"] = row[1]
                minirib["extrados_start"] = row[2]
                end_cm = row[3]
                minirib["end_distance"] = end_cm / 100 if end_cm > 0 else 0.02
                minirib["transition_length"] = row[4]
                minirib["cells"] = row[-1]
                minirib["name"] = "minirib" 
                ParametricGlider.elements["miniribs"].append(minirib)

    def get_row(self, n_row):
        str_row = [
            self.table.item(n_row, i).text()
            for i in range(6)
            if self.table.item(n_row, i)
        ]
        str_row = [item for item in str_row if item != ""]
        if len(str_row) != 6:
            return None
        try:
            # Replace comma with dot for French locale decimal separator
            float_values = [float(s.replace(',', '.')) for s in str_row[:-1]]
            cell_values = list(map(int, str_row[-1].replace(' ', '').split(",")))
            return float_values + [cell_values]
        except (TypeError, ValueError) as e:
            print(e)
            print("something wrong with row " + str(n_row))
            return None
