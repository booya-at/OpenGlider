# coding=utf-8
import collections

from openglider.airfoil import get_x_value
from openglider.plots import sewing_config, PlotPart
from openglider.vector import PolyLine2D


def get_ribs(glider):
    ribs = collections.OrderedDict()
    xvalues = glider.profile_x_values

    for i, rib in enumerate(glider.ribs[glider.has_center_cell:-1]):
        rib_no = i + glider.has_center_cell
        chord = rib.chord

        profile = rib.profile_2d.copy()
        profile.scale(chord)

        profile_outer = profile.copy()
        profile_outer.add_stuff(0.01)

        def get_points(x_value):
            """Return points for sewing marks"""
            ik = get_x_value(xvalues, x_value)
            return profile[ik], profile_outer[ik]

        rib_marks = []

        ############# wieder ein kommentieren

        # marks for attachment-points
        attachment_points = filter(lambda p: p.rib == rib,
                                   glider.attachment_points)
        mark = sewing_config["marks"]["attachment-point"]
        for point in attachment_points:
            rib_marks += mark(*get_points(point.rib_pos))

        # marks for panel-cuts
        rib_cuts = set()
        left_cell = glider.cells[rib_no - (rib_no > 0)]
        right_cell = glider.cells[rib_no]
        for panel in left_cell.panels:
            rib_cuts.add(panel.cut_front["right"])  # left cell
            rib_cuts.add(panel.cut_back["right"])
        for panel in right_cell.panels:
            rib_cuts.add(panel.cut_front["left"])
            rib_cuts.add(panel.cut_back["left"])
        rib_cuts.remove(1)
        rib_cuts.remove(-1)
        for cut in rib_cuts:
            rib_marks += sewing_config["marks"]["panel-cut"](
                *get_points(cut))

        # general marks

        # holes
        cuts = []
        for hole in rib.holes:
            cuts.append(hole.get_flattened(rib))

        # drib cuts
        # TODO

        # outer rib
        cuts.append(cut_outer_rib(profile_outer, profile, sewing_config["allowance"]["trailing_edge"]))

        # add text, entry, holes
        # TODO

        ribs[rib] = PlotPart({"CUTS": cuts,
                              "MARKS": [profile] + rib_marks},
                             name="Rib{}".format(rib_no))

    return ribs


def cut_outer_rib(outer_rib, inner_rib, t_e_allowance):
    """
    Cut trailing edge of outer rib
    """
    p1 = inner_rib[0] + [0, 1]
    p2 = inner_rib[0] + [0, -1]
    cuts = outer_rib.new_cut(p1, p2)

    start = next(cuts)
    stop = next(cuts)
    buerzl = PolyLine2D([outer_rib[stop],
                        outer_rib[stop] + [t_e_allowance, 0],
                        outer_rib[start] + [t_e_allowance, 0],
                        outer_rib[start]])
    return PolyLine2D(outer_rib[start:stop].data) + buerzl


def insert_drib_marks(glider, rib_plots):

    def insert_mark(cut_front, cut_back, rib):
        rib_plot = rib_plots[rib]
        if cut_front[1] == -1 and cut_back[1] == -1:
            # todo: mark( triangle,..)
            ik1 = rib.profile_2d(cut_front[0])
            ik2 = rib.profile_2d(cut_back[0])
            mark = sewing_config["marks"]["diagonal"](0,0)
            mark = None
        elif cut_front[1] == 1 and cut_back[1] == 1:
            mark = None
        else:
            # line
            p1 = None
            p2 = None
            #mark = PolyLine2D([p1, p2])
            mark = None

        if mark:
            rib_plot["MARKS"].append(mark)

    for cell in glider.cells:
        for diagonal in cell.diagonals:
            insert_mark(diagonal.left_front, diagonal.left_back, cell.rib1)
            insert_mark(diagonal.right_front, diagonal.right_back, cell.rib2)