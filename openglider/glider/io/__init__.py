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

from openglider.glider.io import import_geometry, export_3d

IMPORT_GEOMETRY = {
    'ods': import_geometry.import_ods,
    'xls': import_geometry.import_xls
}

EXPORT_3D = {
    'obj': export_3d.export_obj,
    'dxf': export_3d.export_dxf,
    'inp': export_3d.export_apame
}

