from openglider.plots.sketches.sketches import design_plot, vectorstraps_plot
from openglider.plots.sketches.diagonal import diagonal_plot

def get_all_plots(glider_2d, glider_3d=None):
    glider_3d = glider_3d or glider_2d.get_glider_3d()

    return {
        "design_upper": design_plot(glider_2d, glider_3d, lower=False),
        "design_lower": design_plot(glider_2d, glider_3d, lower=True),
        "straps": vectorstraps_plot(glider_2d, glider_3d),
        "diagonals": diagonal_plot(glider_2d, glider_3d)
    }