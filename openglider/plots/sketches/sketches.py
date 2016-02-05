from openglider.plots import PlotPart

from openglider.plots.sketches.design import design_plot
from openglider.vector import PolyLine2D

def shape_plot(glider2d, glider3d=None):
    glider3d = glider3d or glider2d.get_glider_3d()

    for cell_no, cell in enumerate(glider3d.cells):
        pass


def vectorstraps_plot(glider2d, glider3d=None):
    glider3d = glider3d or glider2d.get_glider_3d()
    shape = glider2d.shape

    drawingarea = design_plot(glider2d, glider3d, lower=True)

    for cell_no, cell in enumerate(glider3d.cells):
        for tensionstrap in cell.straps:
            p1 = shape.get_shape_point(cell_no, tensionstrap.left)
            p2 = shape.get_shape_point(cell_no+1, tensionstrap.left)
            drawingarea.parts.append(PlotPart(marks=[PolyLine2D([p1, p2])]))

    return drawingarea


def diagonal_plot(glider2d, glider3d=None):
    glider3d = glider3d or glider2d.get_glider_3d()
    shape = glider2d.shape
    drawingarea = design_plot(glider2d, glider3d, lower=True)

    for cell_no, cell in enumerate(glider3d.cells):
        for diagonal in cell.diagonals:
            left = [p[0] for p in (diagonal.left_front, diagonal.left_back)]
            right = [p[0] for p in (diagonal.right_front, diagonal.right_back)]

            points_left = [shape.get_shape_point(cell_no, p) for p in left]
            points_right = [shape.get_shape_point(cell_no+1, p) for p in right]

            drawingarea.parts.append(PlotPart(marks=[PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

    return drawingarea

