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
import Mesh
import numpy as np

class LoadGlider:
    def GetResources(self):
        return {'Pixmap': 'glider_import.svg', 'MenuText': 'creates a glider!!!', 'ToolTip': 'creates a glider'}

    def IsActive(self):
        if FreeCAD.ActiveDocument is None:
            return False
        else:
            return True

    def Activated(self):
        pol=np.loadtxt(FreeCAD.getHomePath()+'Mod/glider/examples/p.dat', dtype=int)
        nod=np.loadtxt(FreeCAD.getHomePath()+'Mod/glider/examples/n.dat', dtype=float)
        planarMesh = []
        for i in pol:
            planarMesh.append(nod[i[0]])
            planarMesh.append(nod[i[1]])
            planarMesh.append(nod[i[2]])
            planarMesh.append(nod[i[0]])
            planarMesh.append(nod[i[2]])
            planarMesh.append(nod[i[3]])

        planarMeshObject = Mesh.Mesh(planarMesh)
        Mesh.show(planarMeshObject)