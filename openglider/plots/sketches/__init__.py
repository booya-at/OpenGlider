from typing import Dict, Any
from openglider.glider.project import GliderProject
from openglider.plots.sketches.shapeplot import ShapePlot
from openglider.plots.sketches.lineplan import LinePlan


def get_all_plots(project: GliderProject) -> Dict[str, ShapePlot]:
    design_upper = ShapePlot(project)
    design_upper.draw_design(lower=False)
    design_upper.draw_design(lower=False, left=True)

    design_lower = ShapePlot(project)
    design_lower.draw_design(lower=True)
    design_lower.draw_design(lower=True, left=True)
    design_lower.draw_cells()
    design_lower.draw_cells(left=True)

    lineplan = LinePlan(project)  #.draw_shape().draw_attachment_points()
    lineplan.draw_cells()
    lineplan.draw_cells(left=True)
    lineplan.draw_lines()

    base_shape = ShapePlot(project)
    base_shape.draw_cells()
    base_shape.draw_cells(left=True)
    base_shape.draw_design(lower=True)
    base_shape.draw_design(lower=True, left=True)

    straps = base_shape.copy()
    straps.draw_straps()
    straps.draw_straps(left=True)

    diagonals = base_shape.copy()
    diagonals.draw_diagonals()
    diagonals.draw_diagonals(left=True)


    return {
        "design_upper": design_upper,
        "design_lower": design_lower,
        "lineplan": lineplan,
        "straps": straps,
        "diagonals": diagonals
    }