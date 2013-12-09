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


