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

import openglider.plots.projection
from openglider.plots.cuts import cuts
from openglider.plots.part import PlotPart, DrawingArea, create_svg
from openglider.plots.config import sewing_config
from openglider.plots.glider.cell import get_panels
from openglider.plots.glider.ribs import get_ribs, insert_drib_marks
from openglider.plots.glider.dribs import get_dribs


def flatten_glider(glider, sewing_config=sewing_config):
    plots = {}

    # Panels!
    panels = get_panels(glider)
    ribs = get_ribs(glider)
    dribs = get_dribs(glider)
    insert_drib_marks(glider, ribs)

    plots['panels'] = DrawingArea.create_raster(panels.values())
    plots['ribs'] = DrawingArea.create_raster([ribs.values()])
    plots["dribs"] = DrawingArea.create_raster(dribs)

    return plots


