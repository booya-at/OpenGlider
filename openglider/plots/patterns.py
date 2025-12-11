import datetime
import os
import subprocess
import logging
from typing import List

import openglider.glider
import openglider.plots.spreadsheets
from openglider.plots.spreadsheets import get_glider_data
import openglider.plots.cuts
import openglider.plots.marks

from openglider.vector.drawing import Layout
from openglider.vector.text import Text
from openglider.plots.glider import PlotMaker
from openglider.glider.project import GliderProject
# import openglider.plots.sketches


class PatternsNew(object):
    plotmaker = PlotMaker
    spreadsheet = get_glider_data
    plotmaker = PlotMaker

    class DefaultConf(PlotMaker.DefaultConfig):
        pass

    def __init__(self, project: GliderProject, config=None):
        self.project = project
        self.glider_2d = project.glider
        self.config = self.DefaultConf(config)
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    def __json__(self):
        return {"project": self.project, "config": self.config}

    def _get_sketches(self) -> List[Layout]:
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

        # Mini Ribs Layout
        from openglider.vector.drawing import PlotPart, Layout
        from openglider.vector.text import Text
        from openglider.vector.functions import rotation_2d, norm
        import numpy as np

        minirib_parts = []
        minirib_counter = 0
        
        # Iterate over cells to find miniribs
        if hasattr(self.project.glider_3d, "cells"):
             for cell_idx, cell in enumerate(self.project.glider_3d.cells):
                 if hasattr(cell, "miniribs"):
                     for mr_idx, mr in enumerate(cell.miniribs):
                         try:
                             minirib_counter += 1
                             
                             # Get flattened shape with seam allowance
                             inner, outer = mr.get_flattened_with_allowance(
                                 cell, 
                                 allowance=self.config.allowance_general
                             )
                             if outer is None:
                                 continue
                             
                             # Create unique name: MR_cell_index
                             unique_name = f"MR_{cell_idx+1}_{mr_idx+1}"
                             
                             # Create PlotPart with proper layers
                             part = PlotPart(
                                 name=unique_name,
                                 material_code="miniribs"  # Material code for grouping
                             )
                             
                             # Outer = cut line, Inner = stitch line
                             part.layers["cuts"].append(outer)
                             part.layers["stitches"].append(inner)
                             
                             # Add hole contours to cuts layer
                             hole_contours = mr.get_hole_contours_2d(cell)
                             for hole_contour in hole_contours:
                                 part.layers["cuts"].append(hole_contour)
                             
                             # Add text label in the seam allowance area
                             # Find a good position for text (middle of the shape)
                             inner_pts = list(inner.data)
                             outer_pts = list(outer.data)
                             if len(inner_pts) > 4 and len(outer_pts) > 4:
                                 # Take points from the leading edge area (first quarter)
                                 idx = len(inner_pts) // 8
                                 p_inner = np.array(inner_pts[idx])
                                 p_outer = np.array(outer_pts[idx])
                                 
                                 # Text position between inner and outer
                                 text_center = (p_inner + p_outer) / 2
                                 diff = p_outer - p_inner
                                 
                                 # Create perpendicular direction for text
                                 p1 = text_center
                                 p2 = text_center + rotation_2d(np.pi / 2).dot(diff)
                                 
                                 text_size = norm(diff) * 0.4
                                 text_obj = Text(unique_name, p1, p2, size=text_size, valign=0)
                                 part.layers["text"] += text_obj.get_vectors()
                             
                             minirib_parts.append(part)
                         except Exception as e:
                             print(f"Failed to plot minirib: {e}")
        
        # Arrange miniribs in a row
        if minirib_parts:
            miniribs_layout = Layout.stack_row(
                minirib_parts, 
                self.config.patterns_align_dist_x
            )
            # Add border frame
            miniribs_layout.draw_border(border=0.02)
            miniribs_layout.add_text("miniribs")
        else:
            miniribs_layout = Layout()

        # Reinforcements are now handled by PlotMaker.get_reinforcements() 
        # and placed above the RIBS frame

        drawings: List[Layout] = [
            design_upper.drawing,
            design_lower.drawing,
            lineplan.drawing,
            diagonals.drawing,
            straps.drawing,
            miniribs_layout,
        ]



        drawings_width = max([dwg.width for dwg in drawings])

        # put name and date inside the patterns
        p1 = [0.0, 0.0]
        p2 = [drawings_width, 0.0]
        text_name = Text(self.project.name or "unnamed", p1, p2, valign=1)
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")
        text_date = Text(date_str, p1, p2, valign=0)
        drawings += [
            Layout([x]) for x in [text_date.get_plotpart(), text_name.get_plotpart()]
        ]

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
        all_patterns = plots.get_all_grouped()

        return all_patterns

    def unwrap(self, outdir):
        def fn(filename):
            return os.path.join(outdir, filename)

        # subprocess.call("mkdir -p {}".format(outdir), shell=True)
        try:
            os.mkdir(outdir)
        except FileExistsError as e:
            print("directory {} already exists, overwrite files".format(outdir))

        if self.config.profile_numpoints:
            self.glider_2d.num_profile = self.config.profile_numpoints

        self.logger.info("create sketches")
        drawings = self._get_sketches()
        designs = Layout.stack_column(drawings, self.config.patterns_align_dist_y)

        self.logger.info("create plots")
        all_patterns = self._get_plotfile()
        all_patterns.append_left(
            designs, distance=self.config.patterns_align_dist_x * 2
        )

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
        excel = PatternsNew.spreadsheet(self.project)
        excel.saveas(os.path.join(outdir, "data.ods"))

        openglider.save(self.project, os.path.join(outdir, "project.json"))


class Patterns(PatternsNew):
    def __init__(self, glider2d, config=None):
        project = openglider.glider.GliderProject(glider2d, None)
        super().__init__(project, config)

    def unwrap(self, outdir, glider_3d):
        self.project.glider_3d = glider_3d
        super().unwrap(outdir)
