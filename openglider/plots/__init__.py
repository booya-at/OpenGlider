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
import svgwrite

from openglider.vector.polyline import PolyLine2D
from openglider.airfoil import get_x_value
from openglider.plots import projection, marks
from openglider.plots.cuts import cuts
from openglider.plots.part import PlotPart, DrawingArea
from openglider.plots.text import get_text_vector


# Sign configuration
sewing_config = {
    "marks": {
        "attachment-point": lambda p1, p2: marks.triangle(2 * p1 - p2, p1),  # on the inner-side
        "panel-cut": marks.line
    },
    "allowance_general": 0.01,
    "scale": 1000,
    "layers":
        {"OUTER_CUTS": {
            "id": 'outer',
            "stroke_width": "1",
            "stroke": "green",
            "fill": "none"},
         "SEWING_MARKS": {
             "id": 'marks',
             "stroke_width": "1",
             "stroke": "black",
             "fill": "none"},
         "TEXT": {
             "id": 'text',
             "stroke_width": "1",
             "stroke": "black",
             "fill": "none"},
        }


}


def flattened_cell(cell):
    # assert isinstance(cell, Cell)
    left, right = projection.flatten_list(cell.prof1, cell.prof2)
    left_bal = left.copy()
    right_bal = right.copy()
    ballooning_left = [cell.rib1.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    ballooning_right = [cell.rib2.ballooning[x] for x in cell.rib2.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i] - left[i]
        left_bal.data[i] -= diff * ballooning_left[i]
        right_bal.data[i] += diff * ballooning_right[i]
    return left_bal, left, right, right_bal


def flatten_glider(glider):
    plots = {}

    # Panels!

    parts = []
    xvalues = glider.profile_x_values

    for cell_no, cell in enumerate(glider.cells):
        cell_parts = []
        left_bal, left, right, right_bal = flattened_cell(cell)
        left_out = left_bal.copy()
        right_out = right_bal.copy()
        left_out.add_stuff(-sewing_config["allowance_general"])
        right_out.add_stuff(sewing_config["allowance_general"])
        left_out.check()
        right_out.check()
        for part_no, panel in enumerate(cell.panels):
            front_left = get_x_value(xvalues, panel.cut_front[0])
            back_left = get_x_value(xvalues, panel.cut_back[0])
            front_right = get_x_value(xvalues, panel.cut_front[1])
            back_right = get_x_value(xvalues, panel.cut_back[1])
            cut_front = cuts[panel.cut_front[2] - 1]([[left_bal, front_left],
                                                      [right_bal, front_right]],
                                                     left_out, right_out, -panel.cut_front[3])
            cut_back = cuts[panel.cut_back[2] - 1]([[left_bal, back_left],
                                                    [right_bal, back_right]],
                                                   left_out, right_out, panel.cut_back[3])
            part_cuts = [left_out[cut_front[1]:cut_back[1]] +
                         PolyLine2D(cut_back[0]) +
                         right_out[cut_front[2]:cut_back[2]:-1] +
                         PolyLine2D(cut_front[0])[::-1]]
            part_marks = [left_bal[front_left:back_left] +
                          right_bal[front_right:back_right:-1] +
                          PolyLine2D([left_bal[front_left]])]

            part_text = get_text_vector(" cell_{}_part{} ".format(cell_no, part_no+1),
                                        left_bal[front_left],
                                        right_bal[front_right],
                                        height=0.8)

            part_marks.append(PolyLine2D([left_bal[front_left],
                                          right_bal[front_right]]))

            # add marks for
            # - Attachment Points
            # - periodic indicators
            for attachment_point in filter(lambda p: p.rib is cell.rib1, glider.attachment_points):
                pass




            cell_parts.append(PlotPart({"OUTER_CUTS": part_cuts,
                                   "SEWING_MARKS": part_marks,
                                   "TEXT": part_text
            }))
        parts.append(cell_parts)

    plots['panels'] = DrawingArea.create_raster(parts)


    ##################################RIBS###########################
    #################################################################
    parts = []
    for i, rib in enumerate(glider.ribs[glider.has_center_cell:-1]):
        rib_no = i + glider.has_center_cell
        profile = rib.profile_2d.copy()
        chord = rib.chord
        profile.scale(chord)
        profile_outer = profile.copy()
        profile_outer.add_stuff(0.01)

        def return_points(x_value):
            "Return points for sewing marks"
            ik = get_x_value(xvalues, x_value)
            return profile[ik], profile_outer[ik]

        rib_marks = []

        ############# wieder ein kommentieren

        # marks for attachment-points
        attachment_points = filter(lambda p: p.rib == rib, glider.attachment_points)
        for point in attachment_points:
            rib_marks += sewing_config["marks"]["attachment-point"](*return_points(point.rib_pos))

        # marks for panel-cuts
        rib_cuts = set()
        if rib_no > 0:
            for panel in glider.cells[rib_no - 1].panels:
                rib_cuts.add(panel.cut_front[1])  # left cell
                rib_cuts.add(panel.cut_back[1])
        for panel in glider.cells[rib_no].panels:
            rib_cuts.add(panel.cut_front[0])
            rib_cuts.add(panel.cut_back[0])
        rib_cuts.remove(1)
        rib_cuts.remove(-1)
        for cut in rib_cuts:
            rib_marks += sewing_config["marks"]["panel-cut"](*return_points(cut))

        # general marks

        #add text, entry, holes

        try:
            profile_outer.close()
        except:
            raise LookupError("ahah {}/{}".format(i, rib.profile_2d))
        parts.append(PlotPart({"OUTER_CUTS": [profile_outer],
                               "SEWING_MARKS": [profile] + rib_marks}))

    plots['ribs'] = DrawingArea.create_raster([parts])

    return plots


def create_svg(drawing_area, path):
    drawing = svgwrite.Drawing()
    # svg is shifted downwards
    drawing_area.move([0, -drawing_area.max_y])
    for part in drawing_area.parts:
        part_group = svgwrite.container.Group()

        for layer_name, layer_config in sewing_config["layers"].items():
            if layer_name in part.layer_dict:
                lines = part.return_layer_svg(layer_name, scale=sewing_config["scale"])
                for line in lines:
                    element = svgwrite.shapes.Polyline(line, **layer_config)
                    part_group.add(element)
        drawing.add(part_group)

    with open(path, "w") as output_file:
        return drawing.write(output_file)

        # FLATTENING
        # Dict for layers
        # Flatten all cell-parts
        #   * attachment points
        #   * miniribs
        #   * sewing marks
        # FLATTEN RIBS
        #   * airfoil
        #   * attachment points
        #   * gibus arcs
        #   * holes
        #   * rigidfoils
        #   * sewing marks
        #   ---> SCALE
        # FLATTEN DIAGONALS
        #     * Flatten + add stuff
        #     * Draw marks on ribs