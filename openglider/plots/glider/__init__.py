import collections

from openglider.plots.drawing import Layout
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
        self.ribs = []
        self._cellplotmakers = dict()

    def __json__(self):
        return {
            "glider3d": self.glider_3d,
            "config": self.config,
            "panels": self.panels,
            #"dribs": self.dribs,
            "ribs": self.ribs
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
            self._cellplotmakers[cell] = self.CellPlotMaker(cell,
                                                            self.glider_3d.attachment_points,
                                                            self.config)

        return self._cellplotmakers[cell]

    def get_panels(self):
        self.panels.clear()
        panels_upper = []
        panels_lower = []
        panels = []

        for cell in self.glider_3d.cells:
            pm = self._get_cellplotmaker(cell)
            lower = pm.get_panels_lower()
            upper = pm.get_panels_upper()
            panels_lower.append(lower)
            panels_upper.append(upper)
            panels.append([])

        if self.config.layout_seperate_panels:
            layout_lower = Layout.stack_row(panels_lower, self.config.patterns_align_dist_x)
            layout_lower.rotate(180, radians=False)
            layout_upper = Layout.stack_row(panels_upper, self.config.patterns_align_dist_x)

            self.panels = Layout.stack_row([layout_lower, layout_upper], 2*self.config.patterns_align_dist_x, draw_grid=True)

        else:
            height = 0

            for cell in self.glider_3d.cells:
                lower = self._get_cellplotmaker(cell).get_panels_lower()
                #lower.rotate(180, radians=False)
                upper = self._get_cellplotmaker(cell).get_panels_upper()
                height = max(height, lower.height)
                panels_lower.append(lower)
                panels_upper.append(upper)
                print("jodolo")

            height += self.config.patterns_align_dist_y

            self.panels = Layout.stack_grid([panels_upper, panels_lower], self.config.patterns_align_dist_x, self.config.patterns_align_dist_y)


        return self.panels

    def get_ribs(self, rotate=False):
        from openglider.glider.rib.rib import SingleSkinRib
        self.ribs = []
        for rib in self.glider_3d.ribs:
            if isinstance(rib, SingleSkinRib):
                rib_plot = SingleSkinRibPlot(rib)
            else:
                rib_plot = RibPlot(rib, self.config)

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

    def get_all_grouped(self):
        # create x-raster
        for rib in self.ribs:
            rib.rotate(90, radians=False)

        panels = self.panels
        ribs = Layout.stack_row(self.ribs, self.config.patterns_align_dist_x)
        dribs = Layout.stack_row(self.dribs.values(), self.config.patterns_align_dist_x)
        straps = Layout.stack_row(self.straps.values(), self.config.patterns_align_dist_x)

        panels_grouped = panels.copy().group_materials()
        ribs_grouped = ribs.group_materials()
        dribs_grouped = dribs.group_materials()
        straps_grouped = straps.group_materials()

        panels_border = panels.draw_border(append=False)
        ribs_border = ribs.draw_border(append=False)
        dribs_border = dribs.draw_border(append=False)
        straps_border = straps.draw_border(append=False)

        for material_name, layout in panels_grouped.items():
            layout.parts.append(panels_border.copy())
            layout.add_text("panels_"+material_name)

        for material_name, layout in ribs_grouped.items():
            layout.parts.append(ribs_border.copy())
            layout.add_text("ribs_"+material_name)

        for material_name, layout in dribs_grouped.items():
            layout.parts.append(dribs_border.copy())
            layout.add_text("dribs_"+material_name)

        for material_name, layout in straps_grouped.items():
            layout.parts.append(straps_border.copy())
            layout.add_text("straps_"+material_name)

        panels.add_text("panels_all")



        all_layouts = [panels]
        all_layouts += panels_grouped.values()
        all_layouts += ribs_grouped.values()
        all_layouts += dribs_grouped.values()
        all_layouts += straps_grouped.values()

        return Layout.stack_column(all_layouts, 0.01, center_x=False)

    def unwrap(self):
        self.get_panels()
        self.get_ribs()
        self.get_dribs()
        self.get_straps()
        return self

    def get_all_parts(self):
        parts = []
        for cell in self.panels.values():
            parts += [p.copy() for p in cell]
        for rib in self.ribs:
            parts.append(rib.copy())
        for dribs in self.dribs.values():
            parts += [p.copy() for p in dribs]
        return Layout(parts)

    #def get_all_grouped(self):
    #    return self.get_all_parts().group_materials()

