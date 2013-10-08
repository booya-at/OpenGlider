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
l.pop(l.index('DraftWorkbench'))
map(gui.removeWorkbench,l)

FreeCAD.newDocument()

"""
#class ViewObserver:
#    def logPosition(self, info):
#        down = (info["State"] == "DOWN")
#        up = (info["State"]=="UP")
#        pos = info["Position"]
#        if down:
#            FreeCAD.Console.PrintMessage("on position: ("+str(pos[0])+", "+str(pos[1])+") down\n")
#        elif up:
#            FreeCAD.Console.PrintMessage("on position: ("+str(pos[0])+", "+str(pos[1])+") up\n")
#
#
#from WorkingPlane import plane
#workingplane = plane()
#
#class MoveObserver:
#    def logPosition(self, info):
#        pos = info["Position"]
#        pos3d = workingplane.getGlobalCoords()
#        FreeCAD.Console.PrintMessage("on position: ("+str(pos3d)+")\n")
#
#
#
#
#v=gui.activeDocument().activeView()
#o = ViewObserver()
#u= MoveObserver()
#c = v.addEventCallback("SoButtonEvent",o.logPosition)
#d = v.addEventCallback("SoLocation2Event",u.logPosition)
"""





gui.exec_loop()