import math
from typing import List, TYPE_CHECKING

import euklid
import openglider.glider
from openglider.airfoil import get_x_value
from openglider.plots import marks
from openglider.plots.glider.config import PatternConfig
from openglider.plots.usage_stats import MaterialUsage
from openglider.vector.drawing import PlotPart
from openglider.vector.text import Text

if TYPE_CHECKING:
    from openglider.glider import Glider


class RibPlot(object):
    plotpart: PlotPart
    x_values: List[float]
    inner: euklid.vector.PolyLine2D
    outer: euklid.vector.PolyLine2D

    layer_name_outline = "cuts"
    layer_name_sewing = "sewing"
    layer_name_rigidfoils = "marks"
    layer_name_text = "text"
    layer_name_marks = "marks"
    layer_name_laser_dots = "L0"
    layer_name_crossports = "cuts"

    class DefaultConfig(PatternConfig):
        marks_diagonal_front = marks.Inside(marks.Arrow(left=True, name="diagonal_front"))
        marks_diagonal_back = marks.Inside(marks.Arrow(left=False, name="diagonal_back"))
        marks_laser_diagonal = marks.Dot(0.8)
        marks_laser_attachment_point = marks.Dot(0.2, 0.8)

        marks_strap = marks.Inside(marks.Line(name="strap"))
        marks_attachment_point = marks.OnLine(marks.Rotate(marks.Cross(name="attachment_point"), math.pi / 4))

        marks_controlpoint = marks.Dot(0.2)
        marks_panel_cut = marks.Line(name="panel_cut")
        rib_text_pos = -0.005

        #protoloops = 0.02
        protoloops = False

    def __init__(self, rib, config=None):
        self.rib = rib
        self.config = self.DefaultConfig(config)

        #self.plotpart = self.x_values = self.inner = self.outer = None

    def flatten(self, glider):
        self.plotpart = PlotPart(name=self.rib.name, material_code=str(self.rib.material))
        prof2d = self.rib.get_hull(glider)

        self.x_values = prof2d.x_values
        self.inner = prof2d.curve.scale(self.rib.chord)
        self.inner_normals = self.inner.normvectors()
        self.outer = self.inner.offset(self.config.allowance_general, simple=False)

        self._insert_attachment_points(glider)
        holes = self.insert_holes()

        panel_cuts = set()
        for cell in glider.cells:
            if cell.rib1 == self.rib:
                # panel-cuts
                for panel in cell.panels:
                    panel_cuts.add(panel.cut_front.x_left)
                    panel_cuts.add(panel.cut_back.x_left)

                # diagonals
                for diagonal in cell.diagonals + cell.straps:
                    self.insert_drib_mark(diagonal, False)

            elif cell.rib2 == self.rib:
                for panel in cell.panels:
                    panel_cuts.add(panel.cut_front.x_right)
                    panel_cuts.add(panel.cut_back.x_right)

                for diagonal in cell.diagonals + cell.straps:
                    self.insert_drib_mark(diagonal, True)

        for cut in panel_cuts:
            self.insert_mark(cut, self.config.marks_panel_cut)

        # rigidfoils
        for rigid in self.rib.get_rigidfoils():
            self.plotpart.layers[self.layer_name_rigidfoils].append(rigid.get_flattened(self.rib))

        for curve in self.rib.curves:
            self.plotpart.layers[self.layer_name_rigidfoils].append(curve.get_flattened(self.rib))

        self._insert_text(self.rib.name)
        self.insert_controlpoints()

        # insert cut
        envelope = self.draw_outline(glider)

        area = envelope.get_area()
        for hole in holes:
            area -= hole.get_area()

        self.weight = MaterialUsage().consume(self.rib.material, area)

        self.plotpart.layers[self.layer_name_sewing].append(self.inner)

        return self.plotpart

    def _get_inner_outer(self, x_value):
        ik = get_x_value(self.x_values, x_value)

        #ik = get_x_value(self.x_values, position)
        inner = self.inner.get(ik)
        outer = inner + self.inner_normals.get(ik) * self.config.allowance_general
        #inner = self.inner[ik]
        # outer = self.outer[ik]
        return inner, outer

    def insert_mark(self, position, mark_function, laser=False):
        if hasattr(mark_function, "__func__"):
            mark_function = mark_function.__func__

        if mark_function is None:
            return

        inner, outer = self._get_inner_outer(position)

        if laser:
            layer = self.layer_name_laser_dots
        else:
            layer = self.layer_name_marks

        self.plotpart.layers[layer] += mark_function(inner, outer)

    def insert_controlpoints(self):
        for x in self.config.distribution_controlpoints:
            self.insert_mark(x, self.config.marks_controlpoint)
            self.insert_mark(x, self.config.marks_laser_controlpoint, laser=True)

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
            self.insert_mark(p1[0], self.config.marks_laser_diagonal, laser=True)
            self.insert_mark(p2[0], self.config.marks_laser_diagonal, laser=True)
        elif p1[1] == p2[1] == 1:
            self.insert_mark(-p1[0], self.config.marks_diagonal_back)
            self.insert_mark(-p2[0], self.config.marks_diagonal_front)
            self.insert_mark(-p1[0], self.config.marks_laser_diagonal, laser=True)
            self.insert_mark(-p2[0], self.config.marks_laser_diagonal, laser=True)
        else:
            p1 = self.get_point(*p1)
            p2 = self.get_point(*p2)
            self.plotpart.layers[self.layer_name_marks].append(euklid.vector.PolyLine2D([p1, p2], name=drib.name))

    def insert_holes(self):
        holes = []
        for hole in self.rib.holes:
            for l in hole.get_flattened(self.rib):
                self.plotpart.layers[self.layer_name_crossports].append(l)
                holes.append(l)
        
        return holes

    def draw_outline(self, glider):
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer.fix_errors()
        inner_rib = self.inner
        t_e_allowance = self.config.allowance_trailing_edge
        p1 = inner_rib.nodes[0] + [0, 1]
        p2 = inner_rib.nodes[0] + [0, -1]
        cuts = outer_rib.cut(p1, p2)

        if len(cuts) != 2:
            raise Exception("could not cut airfoil TE")

        start = cuts[0][0]
        stop = cuts[1][0]

        buerzl = [
            outer_rib.get(stop),
            outer_rib.get(stop) + [t_e_allowance, 0],
            outer_rib.get(start) + [t_e_allowance, 0],
            outer_rib.get(start)
            ]

        contour = euklid.vector.PolyLine2D(
            outer_rib.get(start, stop).nodes + buerzl
        )

        self.plotpart.layers[self.layer_name_outline] += [contour]
        return contour

    def _insert_attachment_points(self, glider: "Glider"):
        for attachment_point in glider.lineset.attachment_points:

            rib = self.rib
            if glider.has_center_cell and glider.ribs.index(self.rib) == 0:
                rib = glider.ribs[1]

            if hasattr(attachment_point, "rib") and attachment_point.rib == rib:
                positions = [attachment_point.rib_pos]

                if attachment_point.protoloops:
                    for i in range(attachment_point.protoloops):
                        positions.append(attachment_point.rib_pos + (i+1)*attachment_point.protoloop_distance)
                        positions.append(attachment_point.rib_pos - (i+1)*attachment_point.protoloop_distance)

                for position in positions:
                    self.insert_mark(position, self.config.marks_attachment_point)
                    self.insert_mark(position, self.config.marks_laser_attachment_point, "L0")

    def _insert_text(self, text):
        inner, outer = self._get_inner_outer(self.config.rib_text_pos)
        diff = outer - inner

        p1 = inner + diff * 0.5
        p2 = p1 + euklid.vector.Rotation2D(-math.pi/2).apply(diff)

        _text = Text(text, p1, p2, size=(outer-inner).length()*0.5, valign=0)
        #_text = Text(text, p1, p2, size=0.05)
        self.plotpart.layers[self.layer_name_text] += _text.get_vectors()


class SingleSkinRibPlot(RibPlot):
    skin_cut = None

    def _get_inner_outer(self, x_value):
        # TODO: shift when after the endpoint
        inner, outer = super()._get_inner_outer(x_value)

        if self.skin_cut is None or x_value < self.skin_cut:
            return inner, outer
        else:
            return inner, inner + (inner - outer)

    def _get_singleskin_cut(self, glider):
        if self.skin_cut is None:
            singleskin_cut = None

            for cell in glider.cells:
                # only a back cut can be a singleskin_cut
                # asserts there is only one removed singleskin Panel!
                # maybe asserts no singleskin rib on stabilo
                if cell.rib1 == self.rib:
                    for panel in cell.panels:
                        if panel.cut_back.cut_type == panel.cut_back.CUT_TYPES.singleskin:
                            singleskin_cut = panel.cut_back.x_left
                            break
                if cell.rib2 == self.rib:
                    for panel in cell.panels:
                        if panel.cut_back.cut_type == panel.cut_back.CUT_TYPES.singleskin:
                            singleskin_cut = panel.cut_back.x_right
                            break
            
            if singleskin_cut is None:
                raise ValueError(f"no singleskin cut found for rib: {self.rib.name}")

            self.skin_cut = singleskin_cut

        return self.skin_cut

    def flatten(self, glider):
        self._get_singleskin_cut(glider)
        return super().flatten(glider)

    def draw_outline(self, glider):
        """
        Cut trailing edge of outer rib
        """
        outer_rib = self.outer
        inner_rib = self.inner
        t_e_allowance = self.config.allowance_trailing_edge
        p1 = inner_rib.get(0) + [0, 1]
        p2 = inner_rib.get(0) + [0, -1]
        cuts = outer_rib.cut(p1, p2)

        start = cuts[0][0]
        stop = cuts[-1][0]

        contour = euklid.vector.PolyLine2D([])

        if isinstance(self.rib, openglider.glider.rib.SingleSkinRib):
            # outer is going from the back back until the singleskin cut

            singleskin_cut_left = self._get_singleskin_cut(glider)
            single_skin_cut = self.rib.profile_2d(singleskin_cut_left)

            buerzl = euklid.vector.PolyLine2D([
                inner_rib.get(0),
                inner_rib.get(0) + [t_e_allowance, 0],
                outer_rib.get(start) + [t_e_allowance, 0],
                outer_rib.get(start)
                ])
            contour += outer_rib.get(start, single_skin_cut)
            contour += inner_rib.get(single_skin_cut, stop)
            contour += buerzl

        else:

            buerzl = euklid.vector.PolyLine2D([outer_rib.get(stop),
                                 outer_rib.get(stop) + [t_e_allowance, 0],
                                 outer_rib.get(start) + [t_e_allowance, 0],
                                 outer_rib.get(start)])

            contour += euklid.vector.PolyLine2D(outer_rib.get(start, stop))
            contour += buerzl
        
        return contour
