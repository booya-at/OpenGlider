#!/usr/bin/python2



import sys
try:
	import FreeCAD
	import FreeCADGui as gui
except:
	sys.path.append('/usr/lib/freecad/lib/')
	import FreeCAD
	import FreeCADGui as gui

print("nonix")
gui.showMainWindow()
print("1")
gui.activateWorkbench("gliderWorkbench")
l=gui.listWorkbenches().keys()
l.pop(l.index('gliderWorkbench'))
map(gui.removeWorkbench,l)

#FreeCAD.newDocument()
print("ok1")
gui.exec_loop()
print("ok2")