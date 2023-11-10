import math
from collections.abc import Callable

from openglider.glider.rib.rib import Rib
from openglider.plots import cuts, marks
from openglider.utils.config import Config
from openglider.utils.distribution import Distribution
from openglider.vector.unit import Length


class PatternConfigOld(Config):
    patterns_scale = 1000 # mm
    complete_glider = True
    debug = False
    profile_numpoints = 400

    cut_entry: type[cuts.Cut] = cuts.FoldedCut
    cut_trailing_edge: type[cuts.Cut] = cuts.ParallelCut
    cut_design: type[cuts.Cut] = cuts.Cut3D
    cut_diagonal_fold: type[cuts.Cut] = cuts.FoldedCut
    cut_3d: type[cuts.Cut] = cuts.Cut3D
    cut_round: type[cuts.Cut] = cuts.Cut3D

    midribs = 50

    patterns_align_dist_y = 0.1
    patterns_align_dist_x = patterns_align_dist_y
    patterns_scale = 1000

    allowance_general = 0.006
    allowance_parallel = 0.006
    allowance_orthogonal = 0.006
    allowance_diagonals = 0.006
    allowance_trailing_edge = 0.01
    allowance_entry_open = 0.015

    insert_design_cuts = False

    marks_diagonal_front: marks.Mark = marks.Combine(marks.Inside(marks.Arrow(left=True, name="diagonal_front")), marks.Dot(0.2, 0.8))
    marks_diagonal_back: marks.Mark = marks.Combine(marks.Inside(marks.Arrow(left=False, name="diagonal_back")), marks.Dot(0.2, 0.8))
    marks_diagonal_center: marks.Mark = marks.Combine(marks.Rotate(marks.Arrow(), -math.pi/2), marks.Dot(0.2, 0.8))

    marks_attachment_point: marks.Mark = marks.Combine(
        marks.OnLine(marks.Rotate(marks.Cross(name="attachment_point"), math.pi / 4)),
        marks.Dot(0.2, 0.8)
    )

    marks_strap = marks.Inside(marks.Line(name="strap"))

    distribution_controlpoints: Distribution | Callable[[Rib], Distribution] = Distribution.from_cos_distribution(30)
    marks_controlpoint = marks.Dot(0.2)

    marks_panel_cut = marks.Combine(marks.Line(name="panel_cut"), marks.Dot(0.2, 0.8))
    rib_text_in_seam = False
    rib_text_pos = -0.003

    allowance_design = 0.012  # trailing_edge

    drib_allowance_folds = Length(0.012)
    drib_num_folds = 0
    drib_text_position = 0.1

    strap_num_folds = 0

    insert_attachment_point_text = True

    layout_seperate_panels = True

    def get_controlpoints(self, rib: Rib) -> Distribution:
        if isinstance(self.distribution_controlpoints, Distribution):
            return self.distribution_controlpoints
        
        return self.distribution_controlpoints(rib)


class OtherPatternConfig(PatternConfigOld):
    complete_glider = False
    cut_entry = cuts.SimpleCut
    cut_trailing_edge = cuts.SimpleCut
    cut_design = cuts.SimpleCut
    cut_diagonal_fold = cuts.SimpleCut
    
    rib_text_in_seam = False
    
    allowance_design = 0.006
    drib_allowance_folds = Length("1cm")
    strap_num_folds = 0
    allowance_entry_open = 0.021



    marks_diagonal_front = marks.Dot(0.2, 0.8)
    marks_diagonal_back = marks.Dot(0.2, 0.8)
    marks_diagonal_center = marks.Dot(0.2, 0.8)


class PatternConfig(OtherPatternConfig):
    pass