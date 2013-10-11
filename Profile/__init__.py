from ._Classes import Profile2D, Profile3D
from ._Classes import XFoil

if __name__ == "__main__":
    from PyQt4 import QtGui
    import Graphics as G
    import sys
    app = QtGui.QApplication(sys.argv)
    a = QtGui.QFileDialog()
    filename=a.getOpenFileName()
    p=Profile2D()
    p.Import(filename)
    print(p.Profile)
    p.Numpoints=20
    a=G.Graphics([G.Line(p.Profile)])
    print(a.coordinates)
