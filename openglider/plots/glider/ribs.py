# coding=utf-8
import collections

import numpy

from openglider.airfoil import get_x_value
from openglider.plots import sewing_config, PlotPart, marks
from openglider.vector import PolyLine2D
from openglider.vector.text import Text


class RibPlot:
    allowance_general = None
    allowance_trailing_edge = None

    marks_diagonal_front = marks.inside(marks.arrow_left)
    marks_diagonal_back = marks.inside(marks.arrow_right)
    marks_strap = marks.inside(marks.line)
    marks_attachment_point = marks.on_line(marks.Rotate(marks.cross, numpy.pi / 4))
    marks_panel_cut = marks.line

    def __init__(self, rib, config):
        self.rib = rib
        self.config = config

    def flatten(self):
        self.plotpart = PlotPart(name=self.rib.name, material_code=self.rib.material_code)
        self.x_values = rib.profile_2d.x_values
        self.inner = rib.profile_2d.copy().scale(rib.chord)
        self.outer = self.inner.copy().add_stuff(self.allowance_general)

        # insert cut
        self.cut_outer_rib()
        self.plotpart.layers["stitches"].append(self.inner)

    def insert_mark(self, position, _type):
        mark = self.config["marks"][_type]
        ik = get_x_value(self.x_values, position)
        inner = self.inner[ik]
        outer = self.outer[ik]

        self.plotpart.layers["marks"] += mark(inner, outer)

    def insert_mark_2(self, position, mark_function):
        if mark_function is None:
            return
        ik = get_x_value(self.x_values, position)
        inner = self.inner[ik]
        outer = self.outer[ik]

        self.plotpart.layers["marks"] += mark_function(inner, outer)

    def get_point(self, x, y=-1):
        assert x >= 0
        p = self.rib.profile_2d.profilepoint(x, y)
        return p * self.rib.chord

    def insert_drib_mark(self, drib, right=False):

        if right:
            p1 = drib.right_front
            p2 = drib.right_back
        else:
            p1 = drib.left_front
            p2 = drib.left_back

        if p1[1] == p2[1] == -1:
            self.insert_mark_2(p1[0], self.marks_diagonal_front)
            self.insert_mark(p2[0], self.marks_diagonal_back)
        elif p1[1] == p2[1] == 1:
            self.insert_mark(-p1[0], self.marks_diagonal_back)
            self.insert_mark(-p2[0], self.marks_diagonal_front)
        else:
            p1 = self.get_point(*p1)
            p2 = self.get_point(*p2)
            self.plotpart.layers["marks"].append(PolyLine2D([p1, p2]))

    def cut_outer_rib(self):
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer
        inner_rib = self.inner
        t_e_allowance = self.allowance_trailing_edge
        p1 = inner_rib[0] + [0, 1]
        p2 = inner_rib[0] + [0, -1]
        cuts = outer_rib.new_cut(p1, p2)

        start = next(cuts)
        stop = next(cuts)
        buerzl = PolyLine2D([outer_rib[stop],
                            outer_rib[stop] + [t_e_allowance, 0],
                            outer_rib[start] + [t_e_allowance, 0],
                            outer_rib[start]])
        self.plotpart.layers["cuts"] += [PolyLine2D(outer_rib[start:stop].data) + buerzl]

    def add_text(self, text):
        p1 = self.get_point(0.03, 0)
        p2 = self.get_point(0.13, 0)
        self.plotpart.layers["text"] += Text(text, p1, p2).get_vectors()


def get_ribs(glider):
    ribs = collections.OrderedDict()

    for rib_no, rib in enumerate(glider.ribs[glider.has_center_cell:-1]):
        rib_plot = RibPlot(rib, config=sewing_config)
        rib_no += glider.has_center_cell

        # marks for attachment-points
        attachment_points = filter(lambda p: p.rib == rib,
                                   glider.attachment_points)
        for point in attachment_points:
            rib_plot.insert_mark(point.rib_pos, "attachment-point")

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
        #rib_cuts.remove(1)
        #rib_cuts.remove(-1)
        for cut in rib_cuts:
            rib_plot.insert_mark(cut, "panel-cut")

        # holes
        for hole in rib.holes:
            rib_plot.plotpart.layers["cuts"].append(hole.get_flattened(rib))

        # Diagonals
        for cell in glider.cells:
            if rib in cell.ribs:
                right = False
                if rib is cell.rib2:
                    right = True
                for diagonal in cell.diagonals:
                    rib_plot.insert_drib_mark(diagonal, right)

        for cell in glider.cells:
            for strap in cell.straps:
                if rib is cell.rib1:  # left
                    rib_plot.insert_mark(strap.left, "strap")
                elif rib is cell.rib2:  # right
                    rib_plot.insert_mark(strap.right, "strap")


        # rigidfoils
        for rigid in rib.rigidfoils:
            rib_plot.plotpart.layers["marks"].append(rigid.get_flattened(rib))

        # TEXT
        # TODO: improve (move away from holes?)
        rib_plot.add_text(rib.name)

        ribs[rib] = rib_plot.plotpart

    return ribs
