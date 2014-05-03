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

from __future__ import division
from numpy import dot
import numpy


def flatten(arr, out):
    for i in arr:
        if not isinstance(i, list):
            out.append(i)
        else:
            flatten(i, out)


def proj_force(force, vec):
    proj = dot(vec, force)
    if proj <= 0.00001:
        proj = 0.00001
        print("Divide by zero!!!")
    return dot(force, force) / proj


def proj_to_surface(vec, n_vec):
    print(vec)
    print(n_vec)
    t = -dot(n_vec, vec) / dot(n_vec, n_vec)
    return vec + numpy.array(n_vec) * t


def try_convert(str, form):
    try:
        return form(str)
    except Exception:
        return None


# translate to json input?
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
                        key_dict[current_key][1](line, key_dict[current_key][2], key_dict)  # function from key-dict
                    elif line[0] != "#":
                        print("error in inputfile, line " + str(line_nr))
            else:
                current_key = None
            line_nr += 1
    return key_dict
