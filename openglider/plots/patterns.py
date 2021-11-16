import datetime
import os
import subprocess
import logging
from typing import List, Dict

import openglider.glider
import openglider.plots.spreadsheets
from openglider.plots.spreadsheets import get_glider_data
import openglider.plots.cuts
import openglider.plots.marks
from openglider.plots.usage_stats import MaterialUsage

from openglider.vector.drawing import Layout
from openglider.vector.text import Text
from openglider.plots.glider import PlotMaker
from openglider.glider.project import GliderProject
#import openglider.plots.sketches


class PatternsNew(object):
    spreadsheet = get_glider_data
    plotmaker = PlotMaker

    DefaultConf = PlotMaker.DefaultConfig

    def __init__(self, project: GliderProject, config=None):
        self.project = project
        self.glider_2d = project.glider
        self.config = self.DefaultConf(config)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self.weight: Dict[str, MaterialUsage] = {}

    def __json__(self):
        return {
            "project": self.project,
            "config": self.config
        }

    def _get_sketches(self) -> List[Layout]:
        import openglider.plots.sketches as sketch
        shapeplot = sketch.ShapePlot(self.project)
        design_upper = shapeplot.copy().insert_design(lower=True)
        design_upper.insert_cell_names()
        design_lower = shapeplot.copy().insert_design(lower=False)

        lineplan = shapeplot.copy()
        lineplan.insert_design(lower=True)
        lineplan.insert_attachment_points()
        lineplan.insert_rib_numbers()

        diagonals = sketch.ShapePlot(self.project)
        diagonals.insert_cells()
        diagonals.insert_attachment_points(add_text=False)
        diagonals.insert_diagonals()

        straps = sketch.ShapePlot(self.project)
        straps.insert_cells()
        straps.insert_attachment_points(add_text=False)
        straps.insert_straps()

        drawings: List[Layout] = [design_upper.drawing, design_lower.drawing, lineplan.drawing, diagonals.drawing, straps.drawing]

        drawings_width = max([dwg.width for dwg in drawings])

        # put name and date inside the patterns
        p1 = [0., 0.]
        p2 = [drawings_width, 0.]
        text_name = Text(self.project.name or "unnamed", p1, p2, valign=1)
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")
        text_date = Text(date_str, p1, p2, valign=0)
        drawings += [Layout([x]) for x in [text_date.get_plotpart(), text_name.get_plotpart()]]

        return drawings
    
    def _get_plotfile(self):
        glider = self.project.glider_3d

        if self.config.complete_glider:
            glider = self.project.glider_3d.copy_complete()
            glider.rename_parts()
        else:
            glider = self.project.glider_3d
        

        plots = self.plotmaker(glider, config=self.config)
        glider.lineset.iterate_target_length()
            
        plots.unwrap()
        self.weight = plots.weight
        all_patterns = plots.get_all_grouped()

        return all_patterns

    def unwrap(self, outdir):
        def fn(filename):
            return os.path.join(outdir, filename)

        subprocess.call("mkdir -p {}".format(outdir), shell=True)

        self.logger.info("create sketches")
        drawings = self._get_sketches()
        designs = Layout.stack_column(drawings, self.config.patterns_align_dist_y)

        self.logger.info("create plots")
        all_patterns = self._get_plotfile()
        all_patterns.append_left(designs, distance=self.config.patterns_align_dist_x*2)

        all_patterns.scale(1000)

        all_patterns.export_svg(fn("plots_all.svg"))
        all_patterns.export_dxf(fn("plots_all.dxf"))
        #all_patterns.export_dxf(fn("plots_all_dxf2007.dxf"), "AC1021")
        #all_patterns.export_ntv(fn("plots_all.ntv"))



        # ribs = packer.pack_parts(parts["ribs"].parts, sheet_size=sheet_size)
        # panels = packer.pack_parts(parts["panels"].parts, sheet_size=sheet_size)

        # for sheet_no, sheet in enumerate(ribs):
        #     openglider.plots.create_svg(sheet, fn("ribs_{}".format(sheet_no)))
        # for sheet_no, sheet in enumerate(panels):
        #     openglider.plots.create_svg(sheet, fn("panels_{}".format(sheet_no)))

        sketches = openglider.plots.sketches.get_all_plots(self.project)

        for sketch_name, sketch in sketches.items():
            fill = False
            if sketch_name in ("design_upper", "design_lower"):
                fill=True

            sketch.export_a4(fn(sketch_name+".pdf"), fill=fill)

        self.logger.info("create spreadsheets")
        self.project.glider_3d.lineset.rename_lines()
        excel = PatternsNew.spreadsheet(self.project, consumption=self.weight)
        excel.saveas(os.path.join(outdir, "data.ods"))

        openglider.save(self.project, os.path.join(outdir, "project.json"))


class Patterns(PatternsNew):
    def __init__(self, glider2d, config=None):
        project = openglider.glider.GliderProject(glider2d, None)
        super().__init__(project, config)

    def unwrap(self, outdir, glider_3d):
        self.project.glider_3d = glider_3d
        super().unwrap(outdir)