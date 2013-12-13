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


import FreeCAD
import FreeCADGui as gui
import sys
import os

#clear the terminal
os.system('clear')
#custom prompt
sys.ps1 = ">"
sys.ps2 = '>>'
os.environ['PYTHONINSPECT'] = 'True'

try:
	import readline
except ImportError:
	print("Module readline not available.")
else:
	import rlcompleter
readline.parse_and_bind("tab: complete")


