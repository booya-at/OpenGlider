import collections

from openglider.airfoil import get_x_value
import openglider.plots
from openglider.vector.text import Text
from openglider.plots import sewing_config, cuts, PlotPart
from openglider.vector import PolyLine2D


class PanelPlot:
    def __init__(self, x_values, inner, ballooned, outer, panel):
        self.inner = inner
        self.ballooned = ballooned
        self.outer_orig = outer
        self.outer = [l.copy().check() for l in outer]

        self.panel = panel
        self.xvalues = x_values
        self.plotpart = PlotPart(material_code=self.panel.material_code, name=self.panel.name)

    def get_panel(self):
        allowance = {
            "folded": "entry_open",
            "parallel": "trailing_edge",
            "orthogonal": "general"
        }
        front_left = get_x_value(self.xvalues, self.panel.cut_front["left"])
        back_left = get_x_value(self.xvalues, self.panel.cut_back["left"])
        front_right = get_x_value(self.xvalues, self.panel.cut_front["right"])
        back_right = get_x_value(self.xvalues, self.panel.cut_back["right"])

        allowance_front = allowance[self.panel.cut_front["type"]]
        allowance_back = allowance[self.panel.cut_back["type"]]
        amount_front = -self.panel.cut_front.get("amount",
                                            sewing_config["allowance"][allowance_front])
        amount_back = self.panel.cut_back.get("amount",
                                         sewing_config["allowance"][allowance_back])

        cut_front = cuts[self.panel.cut_front["type"]](
            [[self.ballooned[0], front_left],
             [self.ballooned[1], front_right]],
            self.outer[0], self.outer[1],
            amount_front)
        cut_back = cuts[self.panel.cut_back["type"]](
            [[self.ballooned[0], back_left],
             [self.ballooned[1], back_right]],
            self.outer[0], self.outer[1], amount_back)

        # spitzer schnitt
        # links
        if cut_front[1] >= cut_back[1]:
            cut_front_new = PolyLine2D(cut_front[0])
            ik1, ik2 = cut_front_new.cut_with_polyline(cut_back[0],
                                                       startpoint=0)
            panel_cut = PolyLine2D(cut_back[0])[ik2:]
            panel_cut += self.outer[1][cut_front[2]:cut_back[2]:-1]
            panel_cut += cut_front_new[ik1::-1]
        # rechts
        elif cut_front[2] >= cut_back[2]:
            cut_front_new = PolyLine2D(cut_front[0])
            ik1, ik2 = cut_front_new.cut_with_polyline(cut_back[0],
                                                       startpoint=len(
                                                           cut_front_new) - 1)
            panel_cut = self.outer[0][cut_front[2]:cut_back[2]]
            panel_cut += PolyLine2D(cut_back[0])[:ik2]
            panel_cut += cut_front_new[:ik1:-1]

        else:
            panel_cut = self.outer[0][cut_front[1]:cut_back[1]]
            panel_cut += PolyLine2D(cut_back[0])
            panel_cut += self.outer[1][cut_front[2]:cut_back[2]:-1]
            panel_cut += PolyLine2D(cut_front[0])[::-1]

        panel_cut += PolyLine2D([panel_cut[0]])

        self.plotpart.stitches += [self.ballooned[0][front_left:back_left],
                                   self.ballooned[1][front_right:back_right]]

        self.plotpart.marks += [PolyLine2D([self.ballooned[0][front_left], self.ballooned[1][front_right]]),
                                PolyLine2D([self.ballooned[0][back_left], self.ballooned[1][back_right]])]




        #self.plotpart.marks += [self.inner[0][front_left:back_left] +
        #              self.inner[1][front_right:back_right:-1] +
        #              PolyLine2D([self.inner[0][front_left]])]

        self.plotpart.cuts.append(panel_cut)

    def get_point(self, x):
        ik = get_x_value(self.xvalues, x)
        return [lst[ik] for lst in self.ballooned]

    def get_p1_p2(self, x, which):
        which = {"left": 0, "right": 1}[which]
        ik = get_x_value(self.xvalues, x)

        return self.ballooned[which][ik], self.outer_orig[which][ik]

    def insert_text(self):
        left = get_x_value(self.xvalues, self.panel.cut_front["left"])
        right = get_x_value(self.xvalues, self.panel.cut_front["right"])
        text = self.panel.name
        part_text = Text(text,
                         self.ballooned[0][left],
                         self.ballooned[1][right],
                         size=0.01,
                         align="center",
                         valign=0.6,
                         height=0.8).get_vectors()
        self.plotpart.text += part_text

    def insert_attachment_point_text(self, attachment_point, rib="left"):
        align = rib  # (left, right)
        which = rib  # (left, right)
        if self.panel.cut_front[which] <= attachment_point.rib_pos <= self.panel.cut_back[which]:
            left, right = self.get_point(attachment_point.rib_pos)
            self.plotpart.text += Text(" {} ".format(attachment_point.name), left, right,
                                       size=0.01,  # 1cm
                                       align=align, valign=-0.5).get_vectors()
            self.plotpart.marks += [PolyLine2D(self.get_p1_p2(attachment_point.rib_pos, which))]




def flattened_cell(cell):
    # assert isinstance(cell, Cell)
    left, right = openglider.plots.projection.flatten_list(cell.prof1,
                                                           cell.prof2)
    left_bal = left.copy()
    right_bal = right.copy()
    ballooning = [cell.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i] - left[i]
        left_bal.data[i] -= diff * ballooning[i]
        right_bal.data[i] += diff * ballooning[i]
    return [left, right], [left_bal, right_bal]


def get_panels(glider):
    panels = collections.OrderedDict()
    xvalues = glider.profile_x_values

    for cell_no, cell in enumerate(glider.cells):
        cell_parts = []
        inner, ballooned = flattened_cell(cell)
        outer = [line.copy() for line in ballooned]

        outer[0].add_stuff(-sewing_config["allowance"]["general"])
        outer[1].add_stuff(sewing_config["allowance"]["general"])
        #for line in outer:
        #    line.check()

        for part_no, panel in enumerate(cell.panels):
            part_name = "cell_{}_part{}".format(cell_no, part_no + 1)
            panelplot = PanelPlot(xvalues, inner, ballooned, outer, panel)
            try:
                panelplot.get_panel()
            except Exception as e:
                print(part_name)
                raise e

            panelplot.insert_text()

            for attachment_point in glider.attachment_points:
                if attachment_point.rib == cell.rib1:
                    panelplot.insert_attachment_point_text(attachment_point, rib="left")
                elif attachment_point.rib == cell.rib2:
                    panelplot.insert_attachment_point_text(attachment_point, rib="right")

            cell_parts.append(panelplot.plotpart)


            # add marks for
            # - Attachment Points
            # - periodic indicators
        panels[cell] = cell_parts

    return panels