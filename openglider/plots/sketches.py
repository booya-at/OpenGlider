
import openglider.glider
from openglider.plots import PlotPart, DrawingArea
from openglider.vector import PolyLine2D


def design_plot(glider_2d, glider_3d=None, lower=True):
    assert isinstance(glider_2d, openglider.glider.Glider2D)
    glider_3d = glider_3d or glider_2d.get_glider_3d()
    shape = glider_2d.shape()
    drawingarea = DrawingArea()

    for cell_no, cell in enumerate(glider_3d.cells):
        for panel in cell.panels:
            cut_front = [panel.cut_front["left"], panel.cut_front["right"]]
            cut_back = [panel.cut_back["left"], panel.cut_back["right"]]
            if lower and cut_back[0] < 0 and cut_back[1] < 0:
                continue
            if not lower and cut_front[0] > 0 and cut_front[1] > 0:
                continue

            points = cut_back + cut_front
            if not lower:
                points = [-p for p in points]

            shape_points = []
            for p_no, p in enumerate(points):
                if p < 0:
                    p = 0
                shape_points.append(shape.get_point(cell_no + p_no%2, p))

            drawingarea.parts.append(PlotPart(
                cuts=[PolyLine2D(shape_points[:2] + shape_points[2:][::-1] + shape_points[:1])]))

    return drawingarea


def shape_plot(glider2d, glider3d=None):
    glider3d = glider3d or glider2d.get_glider_3d()

    for cell_no, cell in enumerate(glider3d.cells):
        pass


def vectorstraps_plot(glider2d, glider3d=None):
    glider3d = glider3d or glider2d.get_glider_3d()
    shape = glider2d.shape()

    drawingarea = design_plot(glider2d, glider3d, lower=True)

    for cell_no, cell in enumerate(glider3d.cells):
        for tensionstrap in cell.straps:
            p1 = shape.get_point(cell_no, tensionstrap.left)
            p2 = shape.get_point(cell_no+1, tensionstrap.left)
            drawingarea.parts.append(PlotPart(marks=[PolyLine2D([p1, p2])]))

    return drawingarea


def diagonal_plot(glider2d, glider3d=None):
    glider3d = glider3d or glider2d.get_glider_3d()
    shape = glider2d.shape()
    drawingarea = design_plot(glider2d, glider3d, lower=True)

    for cell_no, cell in enumerate(glider3d.cells):
        for diagonal in cell.diagonals:
            left = [p[0] for p in (diagonal.left_front, diagonal.left_back)]
            right = [p[0] for p in (diagonal.right_front, diagonal.right_back)]

            points_left = [shape.get_point(cell_no, p) for p in left]
            points_right = [shape.get_point(cell_no+1, p) for p in right]

            drawingarea.parts.append(PlotPart(marks=[PolyLine2D(points_left + points_right[::-1] + points_left[:1])]))

    return drawingarea

