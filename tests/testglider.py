__author__ = 'simon'
from openglider import glider
import openglider.Graphics

def odf_import_visual_test(path='/home/simon/OpenGlider/tests/demokite.ods'):
    glider1 = glider.Glider()
    glider1.import_from_file(path)
    glider1.close_rib(-1)  # Stabi
    glider2 = glider1.copy()
    glider2.mirror()
    glider2.cells[0].rib2 = glider1.cells[0].rib1  # remove redundant rib-copy
    glider1.cells = glider2.cells[::-1] + glider1.cells  # start from last mirrored towards last normal
    glider1.recalc()
    # TODO: Miniribs for mirrored cells fail
    #new_glider.cells[0].miniribs.append(MiniRib(0.5, 0.7, 1))
    (polygons, points) = glider1.return_polygons(0)

    polygons = [openglider.Graphics.Polygon(polygon) for polygon in polygons]
    openglider.Graphics.Graphics3D(polygons, points)

if __name__ == "__main__":
    odf_import_visual_test()