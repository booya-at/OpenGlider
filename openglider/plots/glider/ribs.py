# coding=utf-8

import numpy

from openglider.airfoil import get_x_value
from openglider.plots import marks
from openglider.plots.drawing import PlotPart
from openglider.plots.glider.config import PatternConfig
from openglider.vector import PolyLine2D
from openglider.vector.functions import rotation_2d, norm
from openglider.vector.text import Text


class RibPlot(object):
    class DefaultConfig(PatternConfig):
        allowance_general = 0.01
        allowance_trailing_edge = 0.02

        marks_diagonal_front = marks.Inside(marks.Arrow(left=True, name="diagonal_front"))
        marks_diagonal_back = marks.Inside(marks.Arrow(left=False, name="diagonal_back"))
        marks_laser_diagonal = marks.Dot(0.8)
        marks_laser_attachment_point = marks.Dot(0.2, 0.8)

        marks_strap = marks.Inside(marks.Line(name="strap"))
        marks_attachment_point = marks.OnLine(marks.Rotate(marks.Cross(name="attachment_point"), numpy.pi / 4))

        marks_controlpoint = marks.Dot(0.2)
        marks_panel_cut = marks.Line(name="panel_cut")
        rib_text_pos = -0.005

    def __init__(self, rib, config=None):
        self.rib = rib
        self.config = self.DefaultConfig(config)

        self.plotpart = self.x_values = self.inner = self.outer = None

    def flatten(self, glider):
        self.plotpart = PlotPart(name=self.rib.name, material_code=self.rib.material_code)
        prof2d = self.rib.getMesh(glider)
        self.x_values = prof2d.x_values
        self.inner = prof2d.copy().scale(self.rib.chord)
        self.outer = self.inner.copy().add_stuff(self.config.allowance_general)

        self._insert_attachment_points(glider.attachment_points)
        self.insert_holes()

        panel_cuts = set()
        for cell in glider.cells:
            if cell.rib1 == self.rib:
                # panel-cuts
                for panel in cell.panels:
                    panel_cuts.add(panel.cut_front["left"])
                    panel_cuts.add(panel.cut_back["left"])

                # diagonals
                for diagonal in cell.diagonals + cell.straps:
                    self.insert_drib_mark(diagonal, False)

            elif cell.rib2 == self.rib:
                for panel in cell.panels:
                    panel_cuts.add(panel.cut_front["right"])
                    panel_cuts.add(panel.cut_back["right"])

                for diagonal in cell.diagonals + cell.straps:
                    self.insert_drib_mark(diagonal, True)

        for cut in panel_cuts:
            #print(cut, self.marks_panel_cut)
            self.insert_mark(cut, self.config.marks_panel_cut)

        # rigidfoils
        for rigid in self.rib.rigidfoils:
            self.plotpart.layers["marks"].append(rigid.get_flattened(self.rib))

        self._insert_text(self.rib.name)
        self.insert_controlpoints()

        # insert cut
        self.cut_trailing_edge(glider)
        self.plotpart.layers["stitches"].append(self.inner)

        return self.plotpart

    def _get_inner_outer(self, x_value):
        ik = get_x_value(self.x_values, x_value)
        inner = self.inner[ik]
        outer = self.outer[ik]
        return inner, outer

    def insert_mark(self, position, mark_function, layer="marks"):
        if hasattr(mark_function, "__func__"):
            mark_function = mark_function.__func__

        if mark_function is None:
            return

        ik = get_x_value(self.x_values, position)
        inner = self.inner[ik]
        outer = self.outer[ik]

        self.plotpart.layers[layer] += mark_function(inner, outer)

    def insert_controlpoints(self):
        for x in self.config.distribution_controlpoints:
            self.insert_mark(x, self.config.marks_controlpoint, layer="marks")
            self.insert_mark(x, self.config.marks_laser_controlpoint, layer="L0")

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
            self.insert_mark(p1[0], self.config.marks_diagonal_front)
            self.insert_mark(p2[0], self.config.marks_diagonal_back)
            self.insert_mark(p1[0], self.config.marks_laser_diagonal, "L0")
            self.insert_mark(p2[0], self.config.marks_laser_diagonal, "L0")
        elif p1[1] == p2[1] == 1:
            self.insert_mark(-p1[0], self.config.marks_diagonal_back)
            self.insert_mark(-p2[0], self.config.marks_diagonal_front)
            self.insert_mark(-p1[0], self.config.marks_laser_diagonal, "L0")
            self.insert_mark(-p2[0], self.config.marks_laser_diagonal, "L0")
        else:
            p1 = self.get_point(*p1)
            p2 = self.get_point(*p2)
            self.plotpart.layers["marks"].append(PolyLine2D([p1, p2], name=drib.name))

    def insert_holes(self):
        for hole in self.rib.holes:
            self.plotpart.layers["cuts"].append(hole.get_flattened(self.rib))

    def cut_trailing_edge(self, glider):
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer
        inner_rib = self.inner
        t_e_allowance = self.config.allowance_trailing_edge
        p1 = inner_rib[0] + [0, 1]
        p2 = inner_rib[0] + [0, -1]
        cuts = outer_rib.cut(p1, p2, extrapolate=True)

        start = next(cuts)[0]
        stop = next(cuts)[0]
        buerzl = PolyLine2D([outer_rib[stop],
                            outer_rib[stop] + [t_e_allowance, 0],
                            outer_rib[start] + [t_e_allowance, 0],
                            outer_rib[start]])

        # get a list of cuts from the left and right side
        # 1. problem1: last cut for single-skin = 1!
        # 2. no way to see if no-panel section is leading-edge or not!



        folded_cuts_from_left = []
        folded_cuts_from_right = []
        for cell in glider.cells:
            if cell.rib1 == self.rib:
                for panel in cell.panels:
                    if panel.cut_front["type"] == "folded":
                        folded_cuts_from_left.append(
                            [panel.cut_front["left"], panel.cut_back["left"]]
                        )

            elif cell.rib2 == self.rib:
                for panel in cell.panels:
                    if panel.cut_front["type"] == "folded":
                        folded_cuts_from_right.append(
                            [panel.cut_front["right"], panel.cut_back["right"]]
                        )

        # join the two lists and only use the space where folded panels are overlapping
        # assume panels from one side are not overlapping
        overlapping_panels = []
        for l_panel in folded_cuts_from_left:
            for r_panel in folded_cuts_from_right:
                c1 = c2 = None
                if (l_panel[1] <= r_panel[0] or
                    r_panel[1] <= l_panel[0]):
                    pass
                else:
                    if l_panel[0] <= r_panel[0]:
                        c1 = r_panel[0]
                    else:
                        c1 = l_panel[0]
                    if l_panel[1] <= r_panel[1]:
                        c2 = l_panel[1]
                    else:
                        c2 = r_panel[1]
                    if (c1 and c2 and c1 != c2):
                        overlapping_panels.append([c1, c2])
        contour = PolyLine2D([])
        panel = None
        for panel in overlapping_panels:
            contour += PolyLine2D(outer_rib[start:panel[0]])
            contour += PolyLine2D(inner_rib[panel[0]:panel[1]])
            start = panel[1]
        contour += PolyLine2D(outer_rib[start:stop])
        contour += buerzl

        self.plotpart.layers["cuts"] += [contour]


    def _insert_attachment_points(self, points):
        for attachment_point in points:
            if hasattr(attachment_point, "rib") and attachment_point.rib == self.rib:
                self.insert_mark(attachment_point.rib_pos, self.config.marks_attachment_point)
                self.insert_mark(attachment_point.rib_pos, self.config.marks_laser_attachment_point, "L0")

    def _insert_text(self, text):
        inner, outer = self._get_inner_outer(self.config.rib_text_pos)
        diff = outer - inner

        p1 = inner + diff/2
        p2 = p1 + rotation_2d(numpy.pi/2).dot(diff)

        _text = Text(text, p1, p2, size=norm(outer-inner)*0.5, valign=0)
        #_text = Text(text, p1, p2, size=0.05)
        self.plotpart.layers["text"] += _text.get_vectors()