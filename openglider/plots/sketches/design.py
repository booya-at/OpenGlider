import openglider.glider
from openglider.vector import PolyLine2D
from openglider.plots.part import DrawingArea, PlotPart


def design_plot(glider_2d, glider_3d=None, lower=True):
    assert isinstance(glider_2d, openglider.glider.Glider2D)
    #glider_3d = glider_3d or glider_2d.get_glider_3d()
    shape = glider_2d.half_shape()  #.copy_complete()
    #glider_3d = glider_3d.copy_complete()
    #shape = shape.copy_complete()
    #shape = glider_2d.shape()
    drawingarea = DrawingArea()

    for cell_no, cell_panels in enumerate(glider_2d.get_panels()):

        def match(panel):
            if lower:
                # -> either on the left or on the right it should go further than 0
                return panel.cut_back["left"] > 0 or panel.cut_back["right"] > 0
            else:
                # should start before zero at least once
                return panel.cut_front["left"] < 0 or panel.cut_front["right"] < 0

        panels = filter(match, cell_panels)
        for panel in panels:

            def get_val(val):
                if lower:
                    return max(val, 0)
                else:
                    return max(-val, 0)

            left_front = get_val(panel.cut_front["left"])
            rigth_front = get_val(panel.cut_front["right"])
            left_back = get_val(panel.cut_back["left"])
            right_back = get_val(panel.cut_back["right"])

            p1 = shape.get_point(cell_no, left_front)
            p2 = shape.get_point(cell_no, left_back)
            p3 = shape.get_point(cell_no+1, right_back)
            p4 = shape.get_point(cell_no+1, rigth_front)

            drawingarea.parts.append(PlotPart(
                cuts=[PolyLine2D([p1, p2, p3, p4, p1])],
                material_code=panel.material_code))

    return drawingarea