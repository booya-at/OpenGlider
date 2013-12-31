__author__ = 'simon'
import os
import sys
try:
    import openglider
except ImportError:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0]))))
from openglider import glider
import openglider.Graphics
testfolder = os.path.dirname(os.path.abspath(__file__))


def odf_import_visual_test(path=testfolder+'/demokite.ods'):
    glider1 = glider.Glider()
    glider1.import_geometry(path)
    glider1.close_rib(-1)  # Stabi
    glider2 = glider1.copy()
    glider2.mirror()
    glider2.cells[-1].rib2 = glider1.cells[0].rib1  # remove redundant rib-copy
    glider1.cells = glider2.cells + glider1.cells  # start from last mirrored towards last normal
    glider1.recalc()
    # TODO: Miniribs for mirrored cells fail
    #new_glider.cells[0].miniribs.append(MiniRib(0.5, 0.7, 1))
    (polygons, points) = glider1.return_polygons(0)

    polygons = [openglider.Graphics.Polygon(polygon) for polygon in polygons]
    openglider.Graphics.Graphics3D(polygons, points)

if __name__ == "__main__":
    odf_import_visual_test()