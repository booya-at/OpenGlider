#!/usr/bin/python2

import sys
import os
try:
	import FreeCAD
	import FreeCADGui as gui
except:
	sys.path.append('/usr/lib/freecad/lib/')
	import FreeCAD
	import FreeCADGui as gui
import numpy as np

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


