import numpy

from openglider.utils import Config
from openglider.utils.distribution import Distribution
from openglider.plots import marks

from openglider.plots.cuts import cuts


class PatternConfig(Config):
    cut_entry = cuts["parallel"]
    cut_trailing_edge =  cuts["parallel"]
    cut_design = cuts["parallel"]

    patterns_align_dist_y = 0.05
    patterns_align_dist_x = patterns_align_dist_y
    patterns_scale = 1000

    allowance_general = 0.01
    allowance_parallel = 0.01
    allowance_orthogonal = 0.01
    allowance_folded = 0.015
    allowance_diagonals = 0.01
    allowance_trailing_edge = 0.02
    allowance_entry_open = 0.015

    marks_diagonal_front = marks.Inside(marks.Arrow(left=True, name="diagonal_front"))
    marks_diagonal_back = marks.Inside(marks.Arrow(left=False, name="diagonal_back"))
    marks_laser_diagonal = marks.Dot(0.8)

    marks_laser_attachment_point = marks.Dot(0.2, 0.8)
    marks_attachment_point = marks.OnLine(marks.Rotate(marks.Cross(name="attachment_point"), numpy.pi / 4))

    marks_strap = marks.Inside(marks.Line(name="strap"))

    distribution_controlpoints = Distribution.from_linear(20, -1, 1)
    marks_laser_controlpoint = marks.Dot(0.2)
    marks_controlpoint = marks.Dot(0.2)

    marks_panel_cut = marks.Line(name="panel_cut")
    rib_text_pos = -0.005

    allowance_design = 0.012  # trailing_edge

    drib_allowance_folds = 0.012
    drib_num_folds = 1
    drib_text_position = 0.1

    insert_attachment_point_text = True

    layout_seperate_panels = True


class OtherPatternConfig(PatternConfig):
    cut_entry = cuts["orthogonal"]
    layout_seperate_panels = False
    #cut_trailing_edge = None
