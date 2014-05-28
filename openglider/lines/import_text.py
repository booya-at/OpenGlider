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


from functions import *
from elements import Line, Node
from openglider.lines import LineSet
from openglider.vector import normalize


# IMPORT TEXT FILE#################
def import_lines(path):
    key_dict = {
        "NODES": [8, store_nodes, []],  # 8 tab-seperated values
        "LINES": [5, store_lines, []],
        "CALCPAR": [5, store_calc_par, {}]
    }
    return import_file(path, key_dict)


def store_nodes(values, thalist, key_dict):
    n = Node(try_convert(values[0], int))
    n.type = try_convert(values[1], int)
    n.vec = numpy.array(map(lambda x: try_convert(x, float), values[2:5]))
    n.force = numpy.array(
        map(lambda x: try_convert(x, float), values[5:8]))
    thalist.append(n)


def store_lines(values, thalist, key_dict):
    lower_no = try_convert(values[1], int)
    upper_no = try_convert(values[2], int)
    upper = key_dict["NODES"][2][upper_no]
    lower = key_dict["NODES"][2][lower_no]
    l = Line(try_convert(values[0], int), upper_node=upper,
             lower_node=lower,  init_length=try_convert(values[3], float))
    thalist.append(l)


def store_calc_par(values, calc_par, key_dict):
    calc_par["GEOSTEPS"] = try_convert(values[0], int)
    calc_par["SAGSTEPS"] = try_convert(values[1], int)
    calc_par["ITER"] = try_convert(values[2], int)
    speed = calc_par["SPEED"] = try_convert(values[3], float)
    glide = calc_par["GLIDE"] = try_convert(values[4], float)
    calc_par["V_INF"] = (
        speed * normalize(numpy.array([glide, 0., 1.])))


def try_convert(str, form):
    try:
        return form(str)
    except Exception:
        return None


def import_file(path, key_dict):
    current_key = None
    with open(path, "r") as lfile:
        line_nr = 1
        for line in lfile:
            line = line.replace("\n", "")
            line = line.replace("\t", " ")
            line = line.split(" ")  # [ 'sfsd', '']
            line = filter(lambda a: a != '', line)  # filter empty elements

            if len(line) > 0:
                if line[0] in key_dict:
                    current_key = line[0]
                elif current_key is not None:
                    if key_dict[current_key][0] == len(line):
                        # function from key-dict
                        key_dict[current_key][1](
                            line, key_dict[current_key][2], key_dict)
                    elif line[0] != "#":
                        print("error in inputfile, line " + str(line_nr))
            else:
                current_key = None
            line_nr += 1
    return key_dict