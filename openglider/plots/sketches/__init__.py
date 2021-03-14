from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.plots.sketches.lineplan import LinePlan


def get_all_plots(project):
    glider_2d = project.glider
    glider_3d = project.glider_3d

    design_upper = ShapePlot(project)
    design_upper.insert_design(lower=False)
    design_upper.insert_design(lower=False, left=True)

    design_lower = ShapePlot(project)
    design_lower.insert_design(lower=True)
    design_lower.insert_design(lower=True, left=True)

    lineplan = LinePlan(project)  #.draw_shape().draw_attachment_points()
    lineplan.insert_lines()

    base_shape = ShapePlot(project)
    base_shape.insert_design(lower=True)
    base_shape.insert_design(lower=True, left=True)

    straps = base_shape.copy()
    straps.insert_straps()
    straps.insert_straps(left=True)

    diagonals = base_shape.copy()
    diagonals.insert_diagonals()
    diagonals.insert_diagonals(left=True)


    return {
        "design_upper": design_upper,
        "design_lower": design_lower,
        "lineplan": lineplan,
        "straps": straps,
        "diagonals": diagonals
    }