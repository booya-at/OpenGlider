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
from typing import List
import re
import json
import logging

import numpy as np

__path__: List[str] = __import__('pkgutil').extend_path(__path__, __name__)

from openglider.config import config
import openglider.jsonify
import openglider.glider
from openglider.version import __version__

logger = logging.getLogger(__name__)

def load(filename):
    """
    """
    if filename.endswith(".ods"):
        res = openglider.glider.GliderProject.import_ods(filename)
    elif filename.lower().endswith(".fcstd") or filename.lower().endswith(".fcstd1"):
        res = openglider.glider.GliderProject.import_freecad(filename)
    else:
        with open(filename) as infile:
            res = openglider.jsonify.load(infile)
        if isinstance(res, dict) and "data" in res:
            logger.info(f"loading file: {filename}")
            logger.info(res["MetaData"])
            
            return res["data"]

    return res

def load_demokite():
    import os
    filename = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests/common/demokite.ods")

    if not os.path.isfile(filename):
        raise FileNotFoundError()

    return load(filename)

def save(data, filename, add_meta=True):
    with open(filename,"w") as outfile:
        openglider.jsonify.dump(data, outfile, add_meta=add_meta)
