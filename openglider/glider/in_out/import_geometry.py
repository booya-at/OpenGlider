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
from openglider.glider.cell import Cell
from openglider.glider.rib import Rib
from openglider.lines import Line, Node


__author__ = 'simon'
import ezodf2 as ezodf
from openglider.glider.ballooning import BallooningBezier
from openglider.airfoil import Profile2D
#from openglider.glider import Glider
import numpy


def import_ods(filename, glider=None):
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets
    # Profiles -> map xvalues
    profiles = [Profile2D(profile) for profile in transpose_columns(sheets[3])]
    xvalues = sorted(profiles, key=lambda prof: prof.numpoints)[0].x_values  # Use airfoil with maximum profilepoints
    for profile in profiles:
        profile.x_values = xvalues
        # Ballooning old : 1-8 > upper (prepend/append (0,0),(1,0)), 9-16 > lower (same + * (1,-1))
    balloonings_temp = transpose_columns(sheets[4])
    balloonings = []
    for baloon in balloonings_temp:
        upper = [[0, 0]] + baloon[:7] + [[1, 0]]
        lower = [[0, 0]] + [[i[0], -1 * i[1]] for i in baloon[8:15]] + [[1, 0]]
        balloonings.append(BallooningBezier([upper, lower]))

    # Data
    data = {}
    datasheet = sheets[-1]
    assert isinstance(datasheet, ezodf.Sheet)
    for i in range(datasheet.nrows()):
        data[datasheet.get_cell([i, 0]).value] = datasheet.get_cell([i, 1]).value
        #print(data["GLEITZAHL"])
    glider.data = data

    cells = []
    main = sheets[0]
    x = y = z = span_last = 0.
    alpha2 = 0.
    thisrib = None
    # TODO: Glide -> DATAIMPORT
    for i in range(1, main.nrows()):
        line = [main.get_cell([i, j]).value for j in range(main.ncols())]
        if not line[0]:
            #print("leere zeile:", i, main.nrows())
            break

        chord = line[1]  # Rib-Chord
        span = line[2]  # spanwise-length (flat)
        alpha1 = alpha2  # angle before the rib
        alpha2 += line[4] * numpy.pi / 180  # angle after the rib
        alpha = (span > 0) * (alpha1 + alpha2) * 0.5 + line[6] * numpy.pi / 180  # rib's angle
        x = line[3]  # x-value -> front/back (ribwise)
        y += numpy.cos(alpha1) * (span - span_last)  # y-value -> spanwise
        z -= numpy.sin(alpha1) * (span - span_last)  # z-axis -> up/down
        aoa = line[5] * numpy.pi / 180
        zrot = line[7] * numpy.pi / 180
        span_last = span

        profile = merge(line[8], profiles)
        ballooning = merge(line[9], balloonings)

        lastrib = thisrib
        thisrib = Rib(profile, ballooning, numpy.array([x, y, z]), chord, alpha, aoa, zrot, data["GLEITZAHL"])
        if i == 1 and y != 0:  # Middle-cell
            #print("midrib!", y)
            lastrib = thisrib.copy()
            lastrib.mirror()
        if lastrib:
            cell = Cell(lastrib, thisrib, [])
            cell.name = "Cell_no"+str(i)
            cells.append(cell)

    if glider:
        glider.cells = cells
        glider.close_rib()
        return
    return cells


def get_lower_aufhaengepunkte(data):
    aufhaengepunkte = {}
    xyz = 0
    for key in data:
        if not key is None:
            if "AHP" in key:
                print("juhuuu")
                pos = int(key[4])
                if key[3].upper() == "X":
                    xyz = 0
                elif key[3].upper() == "Y":
                    xyz = 1
                else:
                    xyz = 2
                if pos not in aufhaengepunkte:
                    aufhaengepunkte[pos] = [None, None, None]
                aufhaengepunkte[pos][xyz] = data[key]
    return aufhaengepunkte


def transpose_columns(sheet=ezodf.Table(), columnswidth=2):
    num = sheet.ncols()
    #if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(num / columnswidth):
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


def tolist_lines(sheet=None):
    num_rows = sheet.nrows
    num_cols = sheet.ncols
    attachment_points_lower = attachment_points_upper = []
    linelist = []
    current_nodes = [None for i in range(num_cols)]
    i = j = 0

    while i < num_rows:
        val = sheet.get_cell([i, j]).value
        if j == 0:  # first floor
            if val != "":
                current_nodes[0] = [attachment_points_lower[sheet.get_cell([i, j]).value - 1]] +\
                                   [None for i in range(num_cols)]
            j += 1
        elif j+2 < num_cols:
            if val == "":
                j += 2
            else:
                lower = current_nodes[j//2]
                if j + 4 >= num_cols or sheet.get_cell([i, j+2]).value == "":  # gallery
                    i += 1
                    j = 0
                    upper = attachment_points_upper[int(val)]
                else:
                    upper = Node(node_type=1)
                    current_nodes[j//2+1] = upper
                    j += 2
                linelist.append(
                    Line(number=1, lower_node=lower, upper_node=upper, line_type=sheet.get_cell))
        elif j+1 >= num_cols:
            j = 0
            i += 1



    return linelist

def read_attachment_points(sheet):
    j = 0
    while j < sheet.ncols:
        if sheet.get_cell([0, j]).value == "AHP":
            pass


def merge(factor, container):
    k = factor % 1
    i = int(factor - k)
    first = container[i]
    if k > 0:
        second = container[i + 1]
        return first * (1 - k) + second * k
    return first


def import_xls():
    pass

