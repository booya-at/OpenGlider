import tempfile
from openglider.airfoil.parametric import BezierProfile2D

from openglider.glider.cell import Cell
from openglider.glider.rib import Rib
from openglider.glider import Glider
from openglider.glider.ballooning import BallooningBezier
from openglider.graphics import Graphics3D, Polygon, Line
from openglider.glider.in_out.export_3d import export_obj


path = "/tmp/cell.obj"
# a tool to optimize a parafoil for a given cell geometry
ar = 0.1 

bal = BallooningBezier()
profile = BezierProfile2D.compute_naca(2412)

rib0 = Rib(profile, [0, -ar / 2, 0], 1, 0., 0., 0., 999999.)
rib1 = Rib(profile, [0, ar / 2, 0], 1, 0., 0., 0., 999999.)
cell1 = Cell(rib0, rib1, bal)
glider = Glider([cell1])
export_obj(glider, path, midribs=40, numpoints=50, floatnum=6, copy=False)