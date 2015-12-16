import collections

from openglider.airfoil import get_x_value
import openglider.plots
from openglider.vector.text import Text
from openglider.plots import sewing_config, cuts, PlotPart
from openglider.vector import PolyLine2D


class PanelPlotMaker:
    allowance_general = 0.012
    allowance_entry_open = 0.015  # entry
    allowance_trailing_edge = 0.012  # design
    allowance_design = 0.012  # trailing_edge

    insert_attachment_point_text = True

    def __init__(self, cell):
        self.cell = cell

        self.inner = None
        self.ballooned = None
        self.outer = None
        self.outer_orig = None

    def flatten_cell(self):
        # assert isinstance(cell, Cell)
        left, right = openglider.plots.projection.flatten_list(self.cell.prof1,
                                                               self.cell.prof2)
        left_bal = left.copy()
        right_bal = right.copy()
        ballooning = [self.cell.ballooning[x] for x in self.cell.rib1.profile_2d.x_values]
        for i in range(len(left)):
            diff = right[i] - left[i]
            left_bal.data[i] -= diff * ballooning[i]
            right_bal.data[i] += diff * ballooning[i]

        self.inner = [left, right]
        self.ballooned = [left_bal, right_bal]

        outer_left = left_bal.copy().add_stuff(-self.allowance_general)
        outer_right = right_bal.copy().add_stuff(self.allowance_general)

        self.outer_orig = [outer_left, outer_right]
        self.outer = [l.copy().check() for l in self.outer_orig]

    def get_panels(self, attachment_points=None):
        attachment_points = attachment_points or []
        cell_parts = []
        self.x_values = self.cell.rib1.profile_2d.x_values
        self.flatten_cell()

        for part_no, panel in enumerate(self.cell.panels):
            plotpart = self.get_panel(panel)
            self.insert_attachment_points(panel, plotpart, attachment_points)
            cell_parts.append(plotpart)

            # add marks for
            # - Attachment Points
            # - periodic indicators

        return cell_parts

    def get_panel(self, panel):
        plotpart = PlotPart(material_code=panel.material_code, name=panel.name)

        cut_allowances = {
            "folded": self.allowance_entry_open,
            "parallel": self.allowance_trailing_edge,
            "orthogonal": self.allowance_design
        }


        front_left = get_x_value(self.x_values, panel.cut_front["left"])
        back_left = get_x_value(self.x_values, panel.cut_back["left"])
        front_right = get_x_value(self.x_values, panel.cut_front["right"])
        back_right = get_x_value(self.x_values, panel.cut_back["right"])

        # allowance fallbacks
        allowance_front = cut_allowances[panel.cut_front["type"]]
        allowance_back = cut_allowances[panel.cut_back["type"]]

        # get allowance from panel
        amount_front = -panel.cut_front.get("amount", allowance_front)
        amount_back = panel.cut_back.get("amount", allowance_back)

        # cuts -> cut-line, index left, index right
        cut_front = cuts[panel.cut_front["type"]](
            [[self.ballooned[0], front_left],
             [self.ballooned[1], front_right]],
            self.outer[0], self.outer[1], amount_front)

        cut_back = cuts[panel.cut_back["type"]](
            [[self.ballooned[0], back_left],
             [self.ballooned[1], back_right]],
            self.outer[0], self.outer[1], amount_back)

        # spitzer schnitt
        # links
        if cut_front[1] >= cut_back[1]:
            cut_front_new = PolyLine2D(cut_front[0])
            ik1, ik2 = cut_front_new.cut_with_polyline(cut_back[0],
                                                       startpoint=0)

            panel_right = PolyLine2D([])
            panel_back = PolyLine2D(cut_back[0])[ik2:]
            panel_left = self.outer[1][cut_front[2]:cut_back[2]:-1]
            panel_front = cut_front_new[ik1::-1]
        # rechts
        elif cut_front[2] >= cut_back[2]:
            cut_front_new = PolyLine2D(cut_front[0])
            ik1, ik2 = cut_front_new.cut_with_polyline(cut_back[0],
                                                       startpoint=len(
                                                           cut_front_new) - 1)

            panel_right = self.outer[0][cut_front[2]:cut_back[2]]
            panel_back = PolyLine2D(cut_back[0])[:ik2]
            panel_left = PolyLine2D([])
            panel_front = cut_front_new[:ik1:-1]

        else:
            panel_right = self.outer[0][cut_front[1]:cut_back[1]]
            panel_back = PolyLine2D(cut_back[0])
            panel_left = self.outer[1][cut_front[2]:cut_back[2]:-1]
            panel_front = PolyLine2D(cut_front[0])[::-1]

        envelope = panel_right + panel_back + panel_left + panel_front
        envelope += PolyLine2D([envelope[0]])

        plotpart.layers["cuts"] = []
        plotpart.layers["envelope"] = [envelope]

        plotpart.layers["stitches"] += [
            self.ballooned[0][front_left:back_left],
            self.ballooned[1][front_right:back_right]]

        plotpart.layers["marks"] += [
            PolyLine2D([self.ballooned[0][front_left], self.ballooned[1][front_right]]),
            PolyLine2D([self.ballooned[0][back_left], self.ballooned[1][back_right]])]

        if False:
            if panel_right:
                right = PolyLine2D([panel_front.last()]) + panel_right + PolyLine2D([panel_back[0]])
                plotpart.layers["cuts"].append(right)

            plotpart.layers["cuts"].append(panel_back)

            if panel_left:
                left = PolyLine2D([panel_back.last()]) + panel_left + PolyLine2D([panel_front[0]])
                plotpart.layers["cuts"].append(left)

            plotpart.layers["cuts"].append(panel_front)
        else:
            plotpart.layers["cuts"].append(envelope)


        self.insert_text(panel, plotpart)

        return plotpart

    def get_point(self, x):
        ik = get_x_value(self.x_values, x)
        return [lst[ik] for lst in self.ballooned]

    def get_p1_p2(self, x, which):
        which = {"left": 0, "right": 1}[which]
        ik = get_x_value(self.x_values, x)

        return self.ballooned[which][ik], self.outer_orig[which][ik]

    def insert_text(self, panel, plotpart):
        left = get_x_value(self.x_values, panel.cut_front["left"])
        right = get_x_value(self.x_values, panel.cut_front["right"])
        text = panel.name
        part_text = Text(text,
                         self.ballooned[0][left],
                         self.ballooned[1][right],
                         size=0.01,
                         align="center",
                         valign=0.6,
                         height=0.8).get_vectors()
        plotpart.layers["text"] += part_text

    def insert_attachment_points(self, panel, plotpart, attachment_points):
        for attachment_point in attachment_points:
            if attachment_point.rib == self.cell.rib1:
                align = "left"
            elif attachment_point.rib == self.cell.rib2:
                align = "right"
            else:
                continue

            which = align

            if panel.cut_front[which] <= attachment_point.rib_pos <= panel.cut_back[which]:
                left, right = self.get_point(attachment_point.rib_pos)

                if self.insert_attachment_point_text:
                    plotpart.layers["text"] += Text(" {} ".format(attachment_point.name), left, right,
                                                    size=0.01,  # 1cm
                                                    align=align, valign=-0.5).get_vectors()

                plotpart.layers["marks"] += [PolyLine2D(self.get_p1_p2(attachment_point.rib_pos, which))]