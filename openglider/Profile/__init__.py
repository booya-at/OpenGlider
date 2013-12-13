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
    p.importdat(filename)
    print(p.Profile)
    p.Numpoints=20
    a=G.Graphics([G.Line(p.Profile)])
    print(a.coordinates)
