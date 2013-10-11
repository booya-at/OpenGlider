#!/usr/bin/python2

import FreeCAD
import FreeCADGui as gui

gui.showMainWindow()
gui.activateWorkbench("gliderWorkbench")
l=gui.listWorkbenches().keys()
l.pop(l.index('gliderWorkbench'))
l.pop(l.index('DraftWorkbench'))
map(gui.removeWorkbench,l)

#FreeCAD.newDocument()





gui.exec_loop()