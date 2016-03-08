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
from openglider.plots.part import PlotPart, DrawingArea
from openglider.plots.glider import PlotMaker


def flatten_glider(glider):
    plots = {}

    # Panels!
    plotter = PlotMaker(glider)
    plotter.unwrap()

    panels = plotter.panels
    ribs = plotter.ribs
    dribs = plotter.dribs

    plots['panels'] = DrawingArea.create_raster(panels.values())
    plots['ribs'] = DrawingArea.create_raster([ribs])
    plots["dribs"] = DrawingArea.create_raster(dribs.values())

    return plots


