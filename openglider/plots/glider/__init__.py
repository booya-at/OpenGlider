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

        all_layouts = [panels]
        all_layouts += panels_grouped
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
