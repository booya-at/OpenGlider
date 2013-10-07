#!/usr/bin/python



import sys
try:
	import FreeCAD
	import FreeCADGui as gui
except:
	sys.path.append('/usr/lib/freecad/lib/')
	import FreeCAD
	import FreeCADGui as gui

gui.showMainWindow()
gui.activateWorkbench("gliderWorkbench")
l=gui.listWorkbenches().keys()
l.pop(l.index('gliderWorkbench'))
map(gui.removeWorkbench,l)

FreeCAD.newDocument()

gui.exec_loop()