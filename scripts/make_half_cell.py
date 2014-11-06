import tempfile

from openglider.glider import Cell, Rib, Glider
from openglider.glider.ballooning import BallooningBezier
from openglider.glider.glider_2d import ParaFoil
from openglider.graphics import Graphics3D, Polygon, Line
from openglider.glider.in_out.export_3d import export_obj


path = "/tmp/cell.obj"
# a tool to optimize a parafoil for a given cell geometry
ar = 0.1 

bal = BallooningBezier()
profile = ParaFoil.compute_naca(2412)

rib0 = Rib(profile, bal, [0, -ar/2*3, 0], 1, 0., 0., 0., 999999.)
rib1 = Rib(profile, bal, [0, -ar/2, 0], 1, 0., 0., 0., 999999.)
rib2 = Rib(profile, bal, [0, ar/2, 0], 1, 0., 0., 0., 999999.)
rib3 = Rib(profile, bal, [0, ar/2*3, 0], 1, 0., 0., 0., 999999.)
cell1 = Cell(rib0, rib1)
cell2 = Cell(rib1, rib2)
cell3 = Cell(rib2, rib3)
glider = Glider([cell1, cell2, cell3])
export_obj(glider, path, midribs=10, numpoints=50, floatnum=6, copy=False)

