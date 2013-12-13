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


import FreeCADGui as Gui
import gliderGui


class gliderWorkbench(Workbench):
    """probe workbench object"""
    MenuText = "glider"
    ToolTip = "glider workbench"
    Icon = "glider_workbench.svg"

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Initialize(self):
        #load the module
        self.appendToolbar("Glider", ["LoadGlider","ChangeShape"])
        self.appendMenu("Glider", ["LoadGlider","ChangeShape"])

        profileitems = ["LoadProfile", "ChangeProfile", "CompareProfile", "MergeProfile", "RunXfoil"]
        self.appendToolbar("Profile", profileitems)
        self.appendMenu("Profile", profileitems)

    def Activated(self):
        pass

    def Deactivated(self):
        pass

Gui.addWorkbench(gliderWorkbench())

# Append the open handler
#FreeCAD.EndingAdd("probe formats (*.bmp *.jpg *.png *.xpm)","probeGui")
