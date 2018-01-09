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
__version__ = '0.01'
__author__ = 'Booya'

import numpy as np

from openglider.config import config
import openglider.jsonify
#import openglider.glider
#from openglider.glider.project import GliderProject


def load(filename):
    """
    """
    with open(filename) as infile:
        res = openglider.jsonify.load(infile)
    if isinstance(res, dict) and "data" in res:
        # print(res["MetaData"])  # HakunaMaData
        return res["data"]

    return res


def save(data, filename, add_meta=True):
    with open(filename,"w") as outfile:
        openglider.jsonify.dump(data, outfile, add_meta=add_meta)


# Monkey-patch numpy cross for pypy
try:
    import __pypy__
    def cross(a,b):
        return np.array([a[1]*b[2]-a[2]*b[1],
                            -a[0]*b[2]+a[2]*b[0],
                            a[0]*b[1]-a[1]*b[0]
                            ])
    np.cross = cross
except ImportError:
    pass