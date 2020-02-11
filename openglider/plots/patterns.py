import datetime
import os
import subprocess
import logging

from openglider import jsonify

import openglider.plots.spreadsheets
import openglider.plots.cuts
import openglider.plots.marks

from openglider.vector.drawing import Layout
from openglider.vector.text import Text
from openglider.plots.glider import PlotMaker
from openglider.glider.project import GliderProject
#import openglider.plots.sketches


class PatternsNew(object):
    class DefaultConf(PlotMaker.DefaultConfig):
        pass

    def __init__(self, project: GliderProject, config=None):
        self.project = project
        self.glider_2d = project.glider
        self.config = self.DefaultConf(config)
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")

    def __json__(self):
        return {
            "project": self.project,
            "config": self.config
        }

    def _get_sketches(self):
        import openglider.plots.sketches as sketch
        shapeplot = sketch.ShapePlot(self.project.glider, self.project.glider_3d)
        design_upper = shapeplot.copy().insert_design(lower=True)
        design_upper.insert_cell_names()
        design_lower = shapeplot.copy().insert_design(lower=False)

        lineplan = shapeplot.copy()
        lineplan.insert_design(lower=True)
        lineplan.insert_attachment_points()
        lineplan.insert_rib_numbers()

        diagonals = sketch.ShapePlot(self.project.glider, self.project.glider_3d)
        diagonals.insert_cells()
        diagonals.insert_attachment_points(add_text=False)
        diagonals.insert_diagonals()

        straps = sketch.ShapePlot(self.glider_2d, self.project.glider_3d)
        straps.insert_cells()
        straps.insert_attachment_points(add_text=False)
        straps.insert_straps()

        drawings = [design_upper.drawing, design_lower.drawing, lineplan.drawing, diagonals.drawing, straps.drawing]

        return drawings

    def unwrap(self, outdir):
        def fn(filename):
            return os.path.join(outdir, filename)

        subprocess.call("mkdir -p {}".format(outdir), shell=True)

        if self.config.profile_numpoints:
            self.glider_2d.num_profile = self.config.profile_numpoints

        glider = self.project.glider_3d

        self.logger.info("create sketches")
        drawings = self._get_sketches()
        drawings_width = max([dwg.width for dwg in drawings])

        # put name and date inside the patterns
        p1 = [0., 0.]
        p2 = [drawings_width, 0.]
        text_name = Text(self.project.name or "unnamed", p1, p2, valign=1)
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")
        text_date = Text(date_str, p1, p2, valign=0)
        drawings += [text_date.get_plotpart(), text_name.get_plotpart()]

        designs = Layout.stack_column(drawings, self.config.patterns_align_dist_y)

        self.logger.info("create plots")
        if self.config.complete_glider:
            glider_complete = glider.copy_complete()
            glider_complete.rename_parts()
            plots = PlotMaker(glider_complete, config=self.config)
            glider_complete.lineset.iterate_target_length()
        else:
            plots = PlotMaker(glider, config=self.config)
            glider.lineset.iterate_target_length()
            
        plots.unwrap()
        all_patterns = plots.get_all_grouped()

        # with open(fn("patterns.json"), "w") as outfile:
        #     jsonify.dump(plots, outfile)
        all_patterns.append_left(designs, distance=self.config.patterns_align_dist_x*2)

        self.logger.info("export patterns")

        all_patterns.scale(1000)
        all_patterns.export_svg(fn("plots_all.svg"))
        all_patterns.export_dxf(fn("plots_all_dxf2000.dxf"))
        all_patterns.export_dxf(fn("plots_all_dxf2007.dxf"), "AC1021")
        all_patterns.export_ntv(fn("plots_all.ntv"))



        # ribs = packer.pack_parts(parts["ribs"].parts, sheet_size=sheet_size)
        # panels = packer.pack_parts(parts["panels"].parts, sheet_size=sheet_size)

        # for sheet_no, sheet in enumerate(ribs):
        #     openglider.plots.create_svg(sheet, fn("ribs_{}".format(sheet_no)))
        # for sheet_no, sheet in enumerate(panels):
        #     openglider.plots.create_svg(sheet, fn("panels_{}".format(sheet_no)))

        # sketches = openglider.plots.sketches.get_all_plots(self.glider_2d, glider)
        #
        # for sketch_name in ("design_upper", "design_lower"):
        #     sketch = sketches.pop(sketch_name)
        #     sketch.drawing.scale_a4()
        #     sketch.drawing.export_svg(fn(sketch_name+".svg"), add_styles=True)
        #
        # for sketch_name, sketch in sketches.items():
        #     sketch.drawing.scale_a4()
        #     sketch.drawing.export_svg(fn(sketch_name+".svg"), add_styles=False)

        self.logger.info("create spreadsheets")
        excel = openglider.plots.spreadsheets.get_glider_data(self.project)
        excel.saveas(os.path.join(outdir, "data.ods"))

        openglider.save(self.project, os.path.join(outdir, "project.json"))


class Patterns(PatternsNew):
    def __init__(self, glider2d, config=None):
        project = openglider.glider.GliderProject(glider2d, None)
        super().__init__(project, config)

    def unwrap(self, outdir, glider_3d):
        self.project.glider_3d = glider_3d
        super().unwrap(outdir)