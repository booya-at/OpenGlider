import collections

from openglider.vector.drawing import Layout
from openglider.plots.glider.cell import CellPlotMaker
from openglider.plots.glider.ribs import RibPlot, SingleSkinRibPlot
from openglider.plots.glider.config import PatternConfig, OtherPatternConfig


class PlotMaker(object):
    CellPlotMaker = CellPlotMaker
    RibPlot = RibPlot
    DefaultConfig = OtherPatternConfig

    def __init__(self, glider_3d, config=None):
        self.glider_3d = glider_3d
        self.config = self.DefaultConfig(config)

        self.panels = Layout()
        self.dribs = collections.OrderedDict()
        self.straps = collections.OrderedDict()
        self.rigidfoils = collections.OrderedDict()
        self.reinforcements = []  # Halfmoons and attachment rod sleeves
        self.rod_sleeves = []  # Profile rod sleeves (extrados/intrados)
        self.ribs = []
        self._cellplotmakers = dict()

    def __json__(self):
        return {
            "glider3d": self.glider_3d,
            "config": self.config,
            "panels": self.panels,
            # "dribs": self.dribs,
            "ribs": self.ribs,
        }

    @classmethod
    def __from_json__(cls, dct):
        ding = cls(dct["glider3d"], dct["config"])
        ding.panels = dct["panels"]
        ding.ribs = dct["ribs"]
        # ding.dribs = dct["dribs"]

        return ding

    def _get_cellplotmaker(self, cell):
        if cell not in self._cellplotmakers:
            self._cellplotmakers[cell] = self.CellPlotMaker(
                cell, self.glider_3d.attachment_points, self.config
            )

        return self._cellplotmakers[cell]

    def _get_text_position_inside(self, points, offset_ratio=0.15):
        """
        Get a text position inside a closed polygon near the top edge.
        Returns (p1, p2) for text placement.
        """
        import numpy as np
        
        if len(points) < 3:
            center = np.mean(points, axis=0) if len(points) > 0 else np.array([0, 0])
            return center, center + np.array([0.01, 0])
        
        points = np.array(points)
        
        # Find bbox
        min_pt = np.min(points, axis=0)
        max_pt = np.max(points, axis=0)
        width = max_pt[0] - min_pt[0]
        height = max_pt[1] - min_pt[1]
        
        # Position text in upper-center area of the shape
        center_x = (min_pt[0] + max_pt[0]) / 2
        # Place text at offset_ratio from top
        text_y = max_pt[1] - height * offset_ratio
        
        p1 = np.array([center_x - width * 0.3, text_y])
        p2 = np.array([center_x + width * 0.3, text_y])
        
        return p1, p2

    def get_panels(self):
        self.panels.clear()
        panels_upper = []
        panels_lower = []

        for cell in self.glider_3d.cells:
            pm = self._get_cellplotmaker(cell)
            lower = pm.get_panels_lower()
            upper = pm.get_panels_upper()
            panels_lower.append(
                Layout.stack_column(lower, self.config.patterns_align_dist_y)
            )
            panels_upper.append(
                Layout.stack_column(upper, self.config.patterns_align_dist_y)
            )

        if self.config.layout_seperate_panels:
            layout_lower = Layout.stack_row(
                panels_lower, self.config.patterns_align_dist_x
            )
            layout_lower.rotate(180, radians=False)
            layout_upper = Layout.stack_row(
                panels_upper, self.config.patterns_align_dist_x
            )

            self.panels = Layout.stack_row(
                [layout_lower, layout_upper], 2 * self.config.patterns_align_dist_x
            )

        else:
            self.panels = Layout.stack_grid(
                [panels_upper, panels_lower],
                self.config.patterns_align_dist_x,
                self.config.patterns_align_dist_y,
            )

        return self.panels

    def get_ribs(self, rotate=False):
        from openglider.glider.rib.rib import SingleSkinRib

        self.ribs = []
        for rib in self.glider_3d.ribs:
            if isinstance(rib, SingleSkinRib):
                rib_plot = SingleSkinRibPlot(rib)
            else:
                rib_plot = self.RibPlot(rib, self.config)

            rib_plot.flatten(self.glider_3d)
            if rotate:
                rib_plot.plotpart.rotate(90, radians=False)
            self.ribs.append(rib_plot.plotpart)

    def get_dribs(self):
        self.dribs.clear()
        for cell in self.glider_3d.cells:
            # missing attachmentpoints []
            dribs = self._get_cellplotmaker(cell).get_dribs()
            self.dribs[cell] = dribs

        return self.dribs

    def get_straps(self):
        self.straps.clear()
        for cell in self.glider_3d.cells:
            # missing attachmentpoints []
            straps = self._get_cellplotmaker(cell).get_straps()
            self.straps[cell] = straps

        return self.straps

    def get_rigidfoils(self):
        # TODO: rib rigids
        self.rigidfoils.clear()

        for cell in self.glider_3d.cells:
            rigidfoils = self._get_cellplotmaker(cell).get_rigidfoils()
            self.rigidfoils[cell] = rigidfoils

        return self.rigidfoils

    def get_reinforcements(self):
        """Get attachment reinforcement parts (halfmoons and their rod sleeves) for 2D export."""
        from openglider.vector.drawing import PlotPart
        from openglider.vector.text import Text
        import numpy as np
        
        self.reinforcements = []
        
        for rib_idx, rib in enumerate(self.glider_3d.ribs):
            if hasattr(rib, "reinforcements") and rib.reinforcements:
                for reinf_idx, reinforcement in enumerate(rib.reinforcements):
                    try:
                        flat = reinforcement.get_flattened(rib)
                        unique_name = reinforcement.name or f"R{rib_idx+1}_{reinf_idx+1}"
                        
                        # Halfmoon part
                        if flat.get('halfmoon') and len(flat['halfmoon'].data) > 0:
                            halfmoon_part = PlotPart(
                                name=unique_name,
                                material_code="reinforcement"
                            )
                            halfmoon_part.layers["cuts"].append(flat['halfmoon'])
                            
                            # Text label inside shape
                            p1, p2 = self._get_text_position_inside(flat['halfmoon'].data, 0.25)
                            text_obj = Text(unique_name, p1, p2, size=0.005, valign=0)
                            halfmoon_part.layers["text"] += text_obj.get_vectors()
                            
                            self.reinforcements.append(halfmoon_part)
                        
                        # Rod sleeve part (for attachments)
                        if flat.get('rod_sleeve') and len(flat['rod_sleeve'].data) > 0:
                            sleeve_part = PlotPart(
                                name=unique_name + "_sleeve",
                                material_code="rod_sleeve"
                            )
                            sleeve_part.layers["cuts"].append(flat['rod_sleeve'])
                            
                            # Text label inside shape
                            p1, p2 = self._get_text_position_inside(flat['rod_sleeve'].data, 0.3)
                            text_obj = Text(unique_name, p1, p2, size=0.003, valign=0)
                            sleeve_part.layers["text"] += text_obj.get_vectors()
                            
                            self.reinforcements.append(sleeve_part)
                            
                    except Exception as e:
                        print(f"Failed to plot reinforcement: {e}")
        
        return self.reinforcements

    def get_rod_sleeves(self):
        """Get profile rod sleeves (extrados/intrados) for 2D export in separate frame."""
        from openglider.vector.drawing import PlotPart
        from openglider.vector.text import Text
        import numpy as np
        
        self.rod_sleeves = []
        
        for rib_idx, rib in enumerate(self.glider_3d.ribs):
            if hasattr(rib, "rod_sleeves") and rib.rod_sleeves:
                for sleeve_idx, sleeve in enumerate(rib.rod_sleeves):
                    try:
                        flat = sleeve.get_flattened(rib)
                        surface_label = "E" if sleeve.surface == 'extrados' else "I"
                        unique_name = f"{rib.name}_{surface_label}{sleeve_idx+1}"
                        
                        if flat is not None and hasattr(flat, 'data') and len(flat.data) > 0:
                            sleeve_part = PlotPart(
                                name=unique_name,
                                material_code=f"{sleeve.surface}_sleeve"
                            )
                            sleeve_part.layers["cuts"].append(flat)
                            
                            # Text label inside shape
                            p1, p2 = self._get_text_position_inside(flat.data, 0.3)
                            text_obj = Text(unique_name, p1, p2, size=0.003, valign=0)
                            sleeve_part.layers["text"] += text_obj.get_vectors()
                            
                            self.rod_sleeves.append(sleeve_part)
                            
                    except Exception as e:
                        print(f"Failed to plot rod sleeve {unique_name}: {e}")
                        import traceback
                        traceback.print_exc()
        
        return self.rod_sleeves

    def get_all_grouped(self) -> Layout:
        # create x-raster
        for rib in self.ribs:
            rib.rotate(90, radians=False)

        panels = self.panels
        ribs = Layout.stack_row(self.ribs, self.config.patterns_align_dist_x)

        def stack_grid(dct):
            layout_lst = [
                Layout.stack_column(p, self.config.patterns_align_dist_y)
                for p in dct.values()
            ]
            return Layout.stack_row(layout_lst, self.config.patterns_align_dist_x)

        dribs = stack_grid(self.dribs)
        straps = stack_grid(self.straps)
        rigidfoils = stack_grid(self.rigidfoils)

        def group(layout, prefix):
            grouped = layout.group_materials()
            border = layout.draw_border(append=False)

            for material_name, material_layout in grouped.items():
                material_layout.parts.append(border.copy())
                material_layout.add_text(f"{prefix}_{material_name}")

            return grouped.values()

        panels_grouped = group(panels.copy(), "panels")
        ribs_grouped = group(ribs, "ribs")
        dribs_grouped = group(dribs, "dribs")
        straps_grouped = group(straps, "straps")

        panels.add_text("panels_all")

        # Add reinforcements layout (halfmoons + attachment sleeves)
        reinforcements_layout = Layout()
        if self.reinforcements:
            reinforcements_layout = Layout.stack_row(
                self.reinforcements, self.config.patterns_align_dist_x
            )
            reinforcements_layout.draw_border(border=0.02)
            reinforcements_layout.add_text("reinforcements")

        # Add rod sleeves layout (profile rod sleeves - separate frame)
        rod_sleeves_layout = Layout()
        if self.rod_sleeves:
            rod_sleeves_layout = Layout.stack_row(
                self.rod_sleeves, self.config.patterns_align_dist_x
            )
            rod_sleeves_layout.draw_border(border=0.02)
            rod_sleeves_layout.add_text("rod_sleeves")

        all_layouts = [panels]
        all_layouts += panels_grouped
        if self.reinforcements:
            all_layouts += [reinforcements_layout]
        if self.rod_sleeves:
            all_layouts += [rod_sleeves_layout]
        all_layouts += ribs_grouped
        all_layouts += dribs_grouped
        all_layouts += straps_grouped
        all_layouts += [rigidfoils]

        return Layout.stack_column(all_layouts, 0.01, center_x=False)

    def unwrap(self):
        self.get_panels()
        self.get_ribs()
        self.get_dribs()
        self.get_straps()
        self.get_rigidfoils()
        self.get_reinforcements()
        self.get_rod_sleeves()
        return self

    def get_all_parts(self):
        parts = []
        for cell in self.panels.values():
            parts += [p.copy() for p in cell]
        for rib in self.ribs:
            parts.append(rib.copy())
        for dribs in self.dribs.values():
            parts += [p.copy() for p in dribs]
        for rigidfoils in self.rigidfoils.values():
            parts += [p.copy() for p in rigidfoils]
        return Layout(parts)

    # def get_all_grouped(self):
    #    return self.get_all_parts().group_materials()
