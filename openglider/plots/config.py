import math

from openglider.utils.config import Config
from openglider.utils.distribution import Distribution
from openglider.plots import marks, cuts

class PatternConfig(Config):
    patterns_scale = 1000 # mm
    complete_glider = True
    debug = False
    profile_numpoints = 400

    cut_entry: object = cuts.FoldedCut
    cut_trailing_edge: object = cuts.ParallelCut
    cut_design: object = cuts.Cut3D
    cut_diagonal_fold: object = cuts.FoldedCut
    cut_3d = cuts.Cut3D
    cut_round = cuts.Cut3D

    midribs = 50

    patterns_align_dist_y = 0.1
    patterns_align_dist_x = patterns_align_dist_y
    patterns_scale = 1000

    allowance_general = 0.01
    allowance_parallel = 0.01
    allowance_orthogonal = 0.01
    allowance_diagonals = 0.01
    allowance_trailing_edge = 0.01
    allowance_entry_open = 0.015


    marks_diagonal_front = marks.Inside(marks.Arrow(left=True, name="diagonal_front"))
    marks_diagonal_back = marks.Inside(marks.Arrow(left=False, name="diagonal_back"))
    marks_laser_diagonal = marks.Dot(0.8)

    marks_laser_attachment_point = marks.Dot(0.2, 0.8)
    marks_attachment_point = marks.OnLine(marks.Rotate(marks.Cross(name="attachment_point"), math.pi / 4))

    marks_strap = marks.Inside(marks.Line(name="strap"))

    distribution_controlpoints = Distribution.from_linear(20, -1, 1)
    marks_laser_controlpoint = marks.Dot(0.2)
    marks_controlpoint = marks.Dot(0.2)

    marks_panel_cut = marks.Line(name="panel_cut")
    rib_text_in_seam = True
    rib_text_pos = -0.005

    allowance_design = 0.012  # trailing_edge

    drib_allowance_folds = 0.012
    drib_num_folds = 1
    drib_text_position = 0.1

    strap_num_folds = 1

    insert_attachment_point_text = True

    layout_seperate_panels = True


class OtherPatternConfig(PatternConfig):
    complete_glider = False
    cut_entry = cuts.SimpleCut
    cut_trailing_edge = cuts.SimpleCut
    cut_design = cuts.SimpleCut
    cut_diagonal_fold = cuts.SimpleCut
    
    layout_seperate_panels = True
    rib_text_in_seam = False
    
    allowance_design = 0.01
    drib_allowance_folds = 0.01
    strap_num_folds = 1
    allowance_entry_open = 0.021
