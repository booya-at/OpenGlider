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
        print('hello')
        pol=np.loadtxt('/usr/lib/freecad/Mod/glider/examples/p.dat',dtype=int)
        nod=np.loadtxt('/usr/lib/freecad/Mod/glider/examples/n.dat',dtype=float)
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