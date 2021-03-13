from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.plots.sketches.lineplan import LinePlan


def get_all_plots(project):
    glider_2d = project.glider
    glider_3d = project.glider_3d

    design_upper = ShapePlot(glider_2d, glider_3d)
    design_upper.insert_design(lower=False)

    design_lower = ShapePlot(glider_2d, glider_3d)
    design_lower.insert_design(lower=True)

    lineplan = ShapePlot(glider_2d, glider_3d)  #.draw_shape().draw_attachment_points()
    lineplan.insert_design(lower=True)
    lineplan.insert_attachment_points()

    straps = ShapePlot(glider_2d, glider_3d)
    straps.insert_design(lower=True)
    straps.insert_straps()

    diagonals = ShapePlot(glider_2d, glider_3d)
    diagonals.insert_design(lower=True)
    diagonals.insert_diagonals()


    return {
        "design_upper": design_upper,
        "design_lower": design_lower,
        "straps": straps,
        "diagonals": diagonals
    }