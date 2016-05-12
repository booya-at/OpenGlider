# coding=utf-8

import numpy

from openglider.airfoil import get_x_value
from openglider.plots import marks
from openglider.plots.drawing import PlotPart
from openglider.vector import PolyLine2D
from openglider.vector.text import Text


class RibPlot:
    allowance_general = None
    allowance_trailing_edge = None

    marks_diagonal_front = marks.Inside(marks.arrow_left)
    marks_diagonal_back = marks.Inside(marks.arrow_right)
    marks_strap = marks.Inside(marks.line)
    marks_attachment_point = marks.OnLine(marks.Rotate(marks.cross, numpy.pi / 4))
    marks_panel_cut = marks.line

    def __init__(self, rib):
        self.rib = rib

        self.plotpart = self.x_values = self.inner = self.outer = None

    def flatten(self, glider):
        self.plotpart = PlotPart(name=self.rib.name, material_code=self.rib.material_code)
        self.x_values = self.rib.profile_2d.x_values
        self.inner = self.rib.profile_2d.copy().scale(self.rib.chord)
        self.outer = self.inner.copy().add_stuff(self.allowance_general)

        self.insert_attachment_points(glider.attachment_points)
        self.insert_holes()

        panel_cuts = set()
        for cell in glider.cells:
            if cell.rib1 == self.rib:
                # panel-cuts
                for panel in cell.panels:
                    panel_cuts.add(panel.cut_front["left"])
                    panel_cuts.add(panel.cut_back["left"])

                # diagonals
                for diagonal in cell.diagonals:
                    self.insert_drib_mark(diagonal, False)
                # straps
                for strap in cell.straps:
                    self.insert_mark(strap.left, self.marks_strap)

            elif cell.rib2 == self.rib:
                for panel in cell.panels:
                    panel_cuts.add(panel.cut_front["right"])
                    panel_cuts.add(panel.cut_back["right"])

                for diagonal in cell.diagonals:
                    self.insert_drib_mark(diagonal, True)
                for strap in cell.straps:
                    self.insert_mark(strap.right, self.marks_strap)

        for cut in panel_cuts:
            #print(cut, self.marks_panel_cut)
            self.insert_mark(cut, self.marks_panel_cut)


        # rigidfoils
        for rigid in self.rib.rigidfoils:
            self.plotpart.layers["marks"].append(rigid.get_flattened(self.rib))

        self.add_text(self.rib.name)

        # insert cut
        self.cut_outer_rib()
        self.plotpart.layers["stitches"].append(self.inner)

        return self.plotpart

    def insert_mark(self, position, mark_function):
        if hasattr(mark_function, "__func__"):
            mark_function = mark_function.__func__

        if mark_function is None:
            return

        ik = get_x_value(self.x_values, position)
        inner = self.inner[ik]
        outer = self.outer[ik]

        #print("mark", mark_function, mark_function(inner, outer))
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
            self.insert_mark(p1[0], self.marks_diagonal_front)
            self.insert_mark(p2[0], self.marks_diagonal_back)
        elif p1[1] == p2[1] == 1:
            self.insert_mark(-p1[0], self.marks_diagonal_back)
            self.insert_mark(-p2[0], self.marks_diagonal_front)
        else:
            p1 = self.get_point(*p1)
            p2 = self.get_point(*p2)
            self.plotpart.layers["marks"].append(PolyLine2D([p1, p2]))

    def insert_holes(self):
        for hole in self.rib.holes:
            self.plotpart.layers["cuts"].append(hole.get_flattened(self.rib))

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

    def insert_attachment_points(self, points):
        for attachment_point in points:
            if attachment_point.rib == self.rib:
                self.insert_mark(attachment_point.rib_pos, self.marks_attachment_point)

    def add_text(self, text):
        p1 = self.get_point(0.03, 0)
        p2 = self.get_point(0.13, 0)
        self.plotpart.layers["text"] += Text(text, p1, p2, size=0.05).get_vectors()