# ! /usr/bin/python2
# -*- coding: utf-8; -*-
#
# (c) 2013 booya (http://booya.at)
#
# This file is part of the OpenGlider project.
#
# OpenGlider is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# OpenGlider is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OpenGlider.  If not, see <http://www.gnu.org/licenses/>.
import os
import subprocess

from openglider import jsonify

import openglider.plots.spreadsheets
from openglider.plots.cuts import cuts
from openglider.plots.drawing import PlotPart, DrawingArea
from openglider.plots.glider import PlotMaker


class Patterns(object):
    class DefaultConf(PlotMaker.DefaultConfig):
        pass

    def __init__(self, glider2d, config=None):
        self.glider_2d = glider2d
        self.config_panel = self.DefaultConf(config)

    def __json__(self):
        return {
            "glider2d": self.glider_2d,
            "config": self.config_panel
        }

    def _get_patterns(self):
        plots = PlotMaker(glider)
        plots.unwrap()

        all_stacked = plots.get_all_stacked()
        all_grouped = plots.get_all_grouped()

        return all_stacked, all_grouped

    def unwrap(self, outdir):
        def fn(filename):
            return os.path.join(outdir, filename)

        subprocess.call("mkdir -p {}".format(outdir), shell=True)
        subprocess.call("mkdir -p {}".format(fn("dxf_2000")), shell=True)
        subprocess.call("mkdir -p {}".format(fn("dxf_2007")), shell=True)
        subprocess.call("mkdir -p {}".format(fn("svg")), shell=True)
        subprocess.call("mkdir -p {}".format(fn("ntv")), shell=True)

        print("get glider 3d")
        glider = self.glider_2d.get_glider_3d()
        glider_complete = glider.copy_complete()
        glider_complete.rename_parts()
        print("flatten glider")

        all_stacked, all_grouped = self._get_patterns()

        with open(fn("patterns.json"), "w") as outfile:
            jsonify.dump(all_stacked, outfile)

        print("packing")

        for material_name, pattern in all_grouped.items():
            #new = packer.QuickPacker(pattern).pack()
            new = pattern.copy()
            new.rasterize()
            new.scale(1000)  # m -> mm

            new.export_svg(fn("svg/plots_{}.svg".format(material_name)))
            new.export_dxf(fn("dxf_2000/plots_{}.dxf".format(material_name)))
            new.export_dxf(fn("dxf_2007/plots_{}.dxf".format(material_name)), "AC1021")
            new.export_ntv(fn("ntv/plots_{}.ntv".format(material_name)))
        #sort_and_pack(outdir, all_parts, sheet_height, part_dist, part_dist)

        stacked_all = DrawingArea()
        for pattern in all_stacked.values():
            stacked_all.join(pattern)

        stacked_all.export_svg(fn("svg/plots_all.svg"))
        stacked_all.export_dxf(fn("dxf_2000/plots_all.dxf"))
        stacked_all.export_dxf(fn("dxf_2007/plots_all.dxf"), "AC1021")
        stacked_all.export_ntv(fn("ntv/plots_all.ntv"))



        # ribs = packer.pack_parts(parts["ribs"].parts, sheet_size=sheet_size)
        # panels = packer.pack_parts(parts["panels"].parts, sheet_size=sheet_size)

        # for sheet_no, sheet in enumerate(ribs):
        #     openglider.plots.create_svg(sheet, fn("ribs_{}".format(sheet_no)))
        # for sheet_no, sheet in enumerate(panels):
        #     openglider.plots.create_svg(sheet, fn("panels_{}".format(sheet_no)))

        print("create sketches")
        import openglider.plots.sketches
        sketches = openglider.plots.sketches.get_all_plots(self.glider_2d, glider)

        for sketch_name in ("design_upper", "design_lower"):
            sketch = sketches.pop(sketch_name)
            sketch.drawing.scale_a4()
            sketch.drawing.export_svg(fn(sketch_name+".svg"), add_styles=True)

        for sketch_name, sketch in sketches.items():
            sketch.drawing.scale_a4()
            sketch.drawing.export_svg(fn(sketch_name+".svg"), add_styles=False)

        print("output spreadsheets")
        excel = openglider.plots.spreadsheets.get_glider_data(glider)
        excel.saveas(os.path.join(outdir, "data.ods"))
