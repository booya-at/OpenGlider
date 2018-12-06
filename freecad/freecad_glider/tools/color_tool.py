from __future__ import division

from PySide import QtGui, QtCore
import numpy as np
import FreeCAD as App

from ._tools import BaseTool, input_field, text_field, coin, hex_to_rgb, rgb_to_hex
from .pivy_primitives_new import Polygon, InteractionSeparator, vector3D


def refresh():
    pass

class ColorTool(BaseTool):
    widget_name = 'Color Tool'
    def __init__(self, obj):
        super(ColorTool, self).__init__(obj)

        self.panels = self.parametric_glider.get_panels()

        # panel.materialcode
        # panel.cut_back
        # panel.cut_front
        # cut_front['left']


        # setup the GUI
        self.setup_widget()
        self.setup_pivy()

    def setup_widget(self):
        self.Qcolore_select = QtGui.QPushButton('select color')
        self.layout.setWidget(0, input_field, self.Qcolore_select)
        self.color_dialog = QtGui.QColorDialog()
        self.Qcolore_select.clicked.connect(self.color_dialog.open)
        self.color_dialog.accepted.connect(self.set_color)

        self.Qcolore_replace = QtGui.QPushButton('replace color')
        self.layout.setWidget(1, input_field, self.Qcolore_replace)
        self.color_replace_dialog = QtGui.QColorDialog()
        self.Qcolore_replace.clicked.connect(self.color_replace_dialog.open)
        self.color_replace_dialog.accepted.connect(self.replace_color)

    def setup_pivy(self):
        # get 2d shape properties

        self.selector = InteractionSeparator()
        self.task_separator += [self.selector]
        x_values = self.parametric_glider.shape.rib_x_values
        if self.parametric_glider.shape.has_center_cell:
            x_values = [-x_values[0]] + x_values
        for i, cell in enumerate(self.panels):
            for j, panel in enumerate(cell):
                p1 = [x_values[i], panel.cut_front['left'], 0.]
                p2 = [x_values[i], panel.cut_back['left'], 0.]
                p3 = [x_values[i + 1], panel.cut_back['right'], 0.]
                p4 = [x_values[i + 1], panel.cut_front['right'], 0.]
                vis_panel = Polygon([p1, p2, p3, p4][::-1], True)
                panel.vis_panel = vis_panel
                if panel.material_code:
                    vis_panel.set_color(hex_to_rgb(panel.material_code))
                self.selector += [vis_panel]

        self.selector.register(self.view)

    def set_color(self):
        color = self.color_dialog.currentColor().getRgbF()[:-1]
        for panel in self.selector.selected_objects:
            panel.set_color(color)

    def replace_color(self):
        assert len(self.selector.selected_objects) == 1
        old_color = self.selector.selected_objects[0].std_col
        color = self.color_replace_dialog.currentColor().getRgbF()[:-1]
        for panel in self.selector.objects:
            if panel.std_col == old_color:
                panel.set_color(color)

    def accept(self):
        self.selector.unregister()
        colors = []
        for cell in self.panels:
            cell_colors = []
            for panel in cell:
                cell_colors.append(rgb_to_hex(panel.vis_panel._std_color))
            colors.append(cell_colors)

        self.parametric_glider.elements['materials'] = colors
        super(ColorTool, self).accept()
        self.update_view_glider()


    def reject(self):
        self.selector.unregister()
        super(ColorTool, self).reject()


class ColorContainer(InteractionSeparator):
    def register(self, view):
        self.view = view
        self.mouse_over = self.view.addEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over_cb)
        self.select = self.view.addEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select_cb)
        self.select_all = self.view.addEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all_cb)

    def unregister(self):
        self.view.removeEventCallbackPivy(
            coin.SoLocation2Event.getClassTypeId(), self.mouse_over)
        self.view.removeEventCallbackPivy(
            coin.SoMouseButtonEvent.getClassTypeId(), self.select)
        self.view.removeEventCallbackPivy(
            coin.SoKeyboardEvent.getClassTypeId(), self.select_all)
