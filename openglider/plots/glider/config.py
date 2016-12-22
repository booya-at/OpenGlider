import numpy

from openglider.utils import Config
from openglider.utils.distribution import Distribution
from openglider.plots import marks, cuts


class PatternConfig(Config):
    complete_glider = True

    cut_entry = cuts.FoldedCut
    cut_trailing_edge = cuts.ParallelCut
    cut_design = cuts.DesignCut

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

    strap_num_folds = 0

    insert_attachment_point_text = True

    layout_seperate_panels = True


class EntryCut(cuts.SimpleCut):
    def __init__(self, amount):
        super(EntryCut, self).__init__(2*amount)


class OtherPatternConfig(PatternConfig):
    cut_entry = EntryCut
    cut_trailing_edge = cuts.SimpleCut
    cut_design = cuts.SimpleCut
    layout_seperate_panels = False
    #cut_trailing_edge = None
