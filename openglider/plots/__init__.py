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
import collections

from openglider.vector.polyline import PolyLine2D
from openglider.airfoil import get_x_value
from openglider.plots import projection, marks
from openglider.plots.cuts import cuts
from openglider.plots.part import PlotPart, DrawingArea, create_svg
from openglider.plots.text import get_text_vector
from openglider.plots.config import sewing_config


# Sign configuration


def flattened_cell(cell):
    # assert isinstance(cell, Cell)
    left, right = projection.flatten_list(cell.prof1, cell.prof2)
    left_bal = left.copy()
    right_bal = right.copy()
    ballooning = [cell.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i] - left[i]
        left_bal.data[i] -= diff * ballooning[i]
        right_bal.data[i] += diff * ballooning[i]
    return left_bal, left, right, right_bal


def get_panels(glider):
    panels = collections.OrderedDict()
    xvalues = glider.profile_x_values

    for cell_no, cell in enumerate(glider.cells):
        cell_parts = []
        left_bal, left, right, right_bal = flattened_cell(cell)
        left_out = left_bal.copy()
        right_out = right_bal.copy()
        left_out.add_stuff(-sewing_config["allowance"]["general"])
        right_out.add_stuff(sewing_config["allowance"]["general"])
        left_out.check()
        right_out.check()
        for part_no, panel in enumerate(cell.panels):
            front_left = get_x_value(xvalues, panel.cut_front["left"])
            back_left = get_x_value(xvalues, panel.cut_back["left"])
            front_right = get_x_value(xvalues, panel.cut_front["right"])
            back_right = get_x_value(xvalues, panel.cut_back["right"])

            amount_front = -panel.cut_front.get("amount", sewing_config["allowance"][panel.cut_front["type"]])
            amount_back = panel.cut_back.get("amount", sewing_config["allowance"][panel.cut_back["type"]])

            cut_front = cuts[panel.cut_front["type"]]([[left_bal, front_left],
                                                       [right_bal, front_right]],
                                                      left_out, right_out, amount_front)
            cut_back = cuts[panel.cut_back["type"]]([[left_bal, back_left],
                                                     [right_bal, back_right]],
                                                    left_out, right_out, amount_back)
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




            cell_parts.append(PlotPart({"CUTS": part_cuts,
                                        "MARKS": part_marks,
                                        "TEXT": part_text
                                        }))
        panels[cell] = cell_parts

    return panels


def get_ribs(glider):
    ribs = collections.OrderedDict()
    xvalues = glider.profile_x_values

    for i, rib in enumerate(glider.ribs[glider.has_center_cell:-1]):
        rib_no = i + glider.has_center_cell
        chord = rib.chord

        profile = rib.profile_2d.copy()
        profile.scale(chord)

        profile_outer = profile.copy()
        profile_outer.add_stuff(0.01)

        rib_parts = filter(lambda el: el.rib is rib, glider.rib_elements)

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
                rib_cuts.add(panel.cut_front["right"])  # left cell
                rib_cuts.add(panel.cut_back["right"])
        for panel in glider.cells[rib_no].panels:
            rib_cuts.add(panel.cut_front["left"])
            rib_cuts.add(panel.cut_back["left"])
        rib_cuts.remove(1)
        rib_cuts.remove(-1)
        for cut in rib_cuts:
            rib_marks += sewing_config["marks"]["panel-cut"](*return_points(cut))

        # general marks

        # holes
        cuts = [profile_outer]
        for hole in rib.holes:
            cuts.append(hole.get_flattened(rib))

        # drib cuts


        #add text, entry, holes

        try:
            profile_outer.close()
        except:
            raise LookupError("ahah {}/{}".format(i, rib.profile_2d))
        ribs[rib] = PlotPart({"CUTS": cuts,
                              "MARKS": [profile] + rib_marks})

    return ribs


def get_dribs(glider):
    dribs = []
    for cell_no, cell in enumerate(glider.cells):
        cell_dribs = []
        for d_no, d_rib in enumerate(cell.diagonals):
            left, right = d_rib.get_flattened(cell)
            left_out = left.copy()
            right_out = right.copy()
            alw = sewing_config["allowance"]["general"]
            alw2 = sewing_config["allowance"]["diagonals"]
            left_out.add_stuff(-alw)
            right_out.add_stuff(alw)

            cut_front = cuts["parallel"]([[left, 0],
                                          [right, 0]],
                                         left_out, right_out, -alw2)
            cut_back = cuts["parallel"]([[left, len(left)-1],
                                         [right, len(right)-1]],
                                        left_out, right_out, alw2)

            print("left", left_out[cut_front[1]:cut_back[1]].get_length())
            part_cuts = [left_out[cut_front[1]:cut_back[1]] +
                         PolyLine2D(cut_back[0]) +
                         right_out[cut_front[2]:cut_back[2]:-1] +
                         PolyLine2D(cut_front[0])[::-1]]
            part_marks = [left + right[::-1] +
                          PolyLine2D([left[0]])]

            text = get_text_vector(" cell_{}_drib_{} ".format(cell_no, d_no),
                                   left[0], right[0])

            cell_dribs.append(PlotPart({"CUTS": part_cuts,
                                        "MARKS": part_marks,
                                        "TEXT": text}))

        dribs.append(cell_dribs)

    return dribs


def insert_drib_marks(glider, rib_plots):

    def insert_mark(cut_front, cut_back, rib):
        rib_plot = rib_plots[rib]
        if cut_front[1] == -1 and cut_back[1] == -1:
            # todo: mark( triangle,..)
            ik1 = rib.profile_2d(cut_front[0])
            ik2 = rib.profile_2d(cut_back[0])
            mark = sewing_config["marks"]["diagonal"](0,0)
            mark = None
        elif cut_front[1] == 1 and cut_back[1] == 1:
            mark = None
        else:
            # line
            p1 = None
            p2 = None
            mark = PolyLine2D([p1, p2])

        rib_plots[rib]["MARKS"].append(mark)

    for cell in glider.cells:
        for diagonal in cell.diagonals:
            insert_mark(diagonal.left_front, diagonal.left_back, cell.rib1)
            insert_mark(diagonal.right_front, diagonal.right_back, cell.rib2)


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


