#! /usr/bin/python2
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
import ezodf
import numpy as np

from openglider.lines import Line, Node, LineSet
from openglider.airfoil import Profile2D
from openglider.glider.cell import Panel, Cell
from openglider.glider.rib import AttachmentPoint, Rib
from openglider.glider.ballooning import BallooningBezier


def import_ods(filename, glider):
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets
    # Profiles -> map xvalues
    profiles = [Profile2D(profile) for profile in transpose_columns(sheets[3])]
    xvalues = sorted(profiles, key=lambda prof: prof.numpoints)[
        0
    ].x_values  # Use airfoil with maximum profilepoints
    for profile in profiles:
        profile.x_values = xvalues

    # Ballooning old : 1-8 > upper (prepend/append (0,0),(1,0)), 9-16 > lower (same + * (1,-1))
    balloonings_temp = transpose_columns(sheets[4])
    balloonings = []
    for baloon in balloonings_temp:
        upper = [[0, 0]] + baloon[:7] + [[1, 0]]
        lower = [[0, 0]] + [[i[0], -1 * i[1]] for i in baloon[8:15]] + [[1, 0]]
        balloonings.append(BallooningBezier(upper, lower))

    # Data
    data = {}
    datasheet = sheets[-1]
    assert isinstance(datasheet, ezodf.Sheet)
    for i in range(datasheet.nrows()):
        data[datasheet.get_cell([i, 0]).value] = datasheet.get_cell([i, 1]).value

    glider.data = data

    cells = []
    main = sheets[0]
    x = y = z = span_last = 0.0
    alpha2 = 0.0
    thisrib = None
    for i in range(1, main.nrows()):
        line = [main.get_cell([i, j]).value for j in range(main.ncols())]
        if not line[0]:
            break  # skip empty line

        chord = line[1]  # Rib-Chord
        span = line[2]  # spanwise-length (flat)
        alpha1 = alpha2  # angle before the rib
        alpha2 += line[4] * np.pi / 180  # angle after the rib
        alpha = (span > 0) * (alpha1 + alpha2) * 0.5 + line[
            6
        ] * np.pi / 180  # rib's angle
        x = line[3]  # x-value -> front/back (ribwise)
        y += np.cos(alpha1) * (span - span_last)  # y-value -> spanwise
        z -= np.sin(alpha1) * (span - span_last)  # z-axis -> up/down
        aoa = line[5] * np.pi / 180
        zrot = line[7] * np.pi / 180
        span_last = span

        profile = merge(line[8], profiles)
        ballooning = merge(line[9], balloonings)

        lastrib = thisrib
        thisrib = Rib(
            profile,
            np.array([x, y, z]),
            chord,
            alpha,
            aoa,
            zrot,
            data["GLIDE"],
            name="Rib ({})".format(i),
        )
        if i == 1 and y != 0:  # Middle-cell
            lastrib = thisrib.copy()
            lastrib.mirror()
        if lastrib:
            cell = Cell(lastrib, thisrib, ballooning)
            cell.name = "Cell_no" + str(i)
            cells.append(cell)

    glider.cells = cells
    glider.close_rib()

    ######################################LINESET######################################################
    attachment_points = [
        AttachmentPoint(glider.ribs[args[0]], args[1], args[2])
        for args in read_elements(sheets[2], "AHP", len_data=2)
    ]
    attachment_points.sort(key=lambda element: element.name)
    attachment_points_lower = get_lower_aufhaengepunkte(glider.data)

    for p in attachment_points:
        p.force = np.array([0, 0, 10])
        p.get_position()

    glider.lineset = tolist_lines(sheets[6], attachment_points_lower, attachment_points)
    glider.lineset.recalc()

    ####################################PANELS##########################################################
    cuts = [
        cut + [1, glider.data["Designzugabe"]]
        for cut in read_elements(sheets[1], "DESIGNO")
    ]
    cuts += [
        cut + [1, glider.data["Designzugabe"]]
        for cut in read_elements(sheets[1], "DESIGNM")
    ]
    cuts += [
        cut + [2, glider.data["EKzugabe"]] for cut in read_elements(sheets[1], "EKV")
    ]
    cuts += [
        cut + [2, glider.data["EKzugabe"]] for cut in read_elements(sheets[1], "EKH")
    ]
    for i, cell in enumerate(
        glider.cells
    ):  # cut = [cell_no, x_left, x_right, cut_type, amount_add]
        cuts_this = [cut for cut in cuts if cut[0] == i]
        cuts_this.sort(key=lambda cut: cut[1])
        cuts_this.sort(key=lambda cut: cut[2])
        # Insert leading-/trailing-edge
        cuts_this.insert(0, [i, -1, -1, 3, glider.data["HKzugabe"]])
        cuts_this.append([i, 1, 1, 3, glider.data["HKzugabe"]])
        cell.panels = []
        for j in range(len(cuts_this) - 1):
            if cuts_this[j][3] != 2 or cuts_this[j + 1][3] != 2:  # skip entry
                cell.panels.append(Panel(cuts_this[j][1:], cuts_this[j + 1][1:]))
    return glider


def get_lower_aufhaengepunkte(data):
    aufhaengepunkte = {}
    xyz = {"X": 0, "Y": 1, "Z": 2}
    for key in data:
        if not key is None and "AHP" in key:
            pos = int(key[4])
            if pos not in aufhaengepunkte:
                aufhaengepunkte[pos] = [None, None, None]
            aufhaengepunkte[pos][xyz[key[3].upper()]] = data[key]
    for node in aufhaengepunkte:
        aufhaengepunkte[node] = Node(0, np.array(aufhaengepunkte[node]))
    return aufhaengepunkte


def transpose_columns(sheet=ezodf.Table(), columnswidth=2):
    num = sheet.ncols()
    # if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(int(num / columnswidth)):
        columns = range(col * columnswidth, (col + 1) * columnswidth)
        element = []
        i = 0
        while i < sheet.nrows():
            row = [sheet.get_cell([i, j]).value for j in columns]
            if sum([j is None for j in row]) == len(row):  # Break at empty line
                break
            i += 1
            element.append(row)
        result.append(element)
    return result


def tolist_lines(sheet, attachment_points_lower, attachment_points_upper):
    num_rows = sheet.nrows()
    num_cols = sheet.ncols()
    linelist = []
    current_nodes = [None for i in range(num_cols)]
    i = j = 0
    count = 0

    while i < num_rows:
        val = sheet.get_cell([i, j]).value
        if j == 0:  # first floor
            if val is not None:
                current_nodes = [
                    attachment_points_lower[int(sheet.get_cell([i, j]).value)]
                ] + [None for __ in range(num_cols)]
            j += 1
        elif j + 2 < num_cols:
            if val is None:
                j += 2
            else:
                lower = current_nodes[j // 2]

                if (
                    j + 4 >= num_cols or sheet.get_cell([i, j + 2]).value is None
                ):  # gallery
                    upper = attachment_points_upper[int(val - 1)]
                    line_length = None
                    i += 1
                    j = 0
                else:
                    upper = Node(node_type=1)
                    current_nodes[j // 2 + 1] = upper
                    line_length = sheet.get_cell([i, j]).value
                    j += 2
                linelist.append(
                    Line(
                        number=count,
                        lower_node=lower,
                        upper_node=upper,
                        v_inf=np.array([10, 0, 0]),
                        target_length=line_length,
                    )
                )  # line_type=sheet.get_cell
                count += 1

        elif j + 2 >= num_cols:
            j = 0
            i += 1

    return LineSet(linelist, v_inf=np.array([10, 0, 0]))


def read_elements(sheet, keyword, len_data=2):
    """
    Return rib/cell_no for the element + data
    """

    elements = []
    j = 0
    while j < sheet.ncols():
        if sheet.get_cell([0, j]).value == keyword:
            for i in range(1, sheet.nrows()):
                line = [sheet.get_cell([i, j + k]).value for k in range(len_data)]
                if line[0] is not None:
                    elements.append([i - 1] + line)
            j += len_data
        else:
            j += 1
    return elements


def merge(factor, container):
    k = factor % 1
    i = int(factor // 1)
    first = container[i]
    if k > 0:
        second = container[i + 1]
        return first * (1 - k) + second * k
    else:
        return first.copy()


def import_xls():
    pass
