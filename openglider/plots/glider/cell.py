import collections

import openglider.plots
from openglider.airfoil import get_x_value
from openglider.utils import Config
from openglider.vector.text import Text
from openglider.plots import cuts, PlotPart
from openglider.vector import PolyLine2D


class PanelPlotMaker:
    class DefaultConf(Config):
        allowance_general = 0.012
        allowance_entry_open = 0.015  # entry
        allowance_trailing_edge = 0.012  # design
        allowance_design = 0.012  # trailing_edge

        allowance_drib_folds = 0.012
        allowance_drib_num_folds = 1

        insert_attachment_point_text = True

    def __init__(self, cell, config=None):
        self.cell = cell
        self.config = self.DefaultConf(config)

        self.inner = None
        self.ballooned = None
        self.outer = None
        self.outer_orig = None

    def _flatten_cell(self):
        # assert isinstance(cell, Cell)
        left, right = openglider.plots.projection.flatten_list(self.cell.prof1,
                                                               self.cell.prof2)
        left_bal = left.copy()
        right_bal = right.copy()
        ballooning = [self.cell.ballooning[x] for x in self.cell.rib1.profile_2d.x_values]
        for i in range(len(left)):
            diff = (right[i] - left[i]) * ballooning[i] / 2
            left_bal.data[i] -= diff
            right_bal.data[i] += diff

        self.inner = [left, right]
        self.ballooned = [left_bal, right_bal]

        outer_left = left_bal.copy().add_stuff(-self.config.allowance_general)
        outer_right = right_bal.copy().add_stuff(self.config.allowance_general)

        self.outer_orig = [outer_left, outer_right]
        self.outer = [l.copy().check() for l in self.outer_orig]

    def get_panels(self, attachment_points=None):
        attachment_points = attachment_points or []
        cell_parts = []
        self.x_values = self.cell.rib1.profile_2d.x_values
        self._flatten_cell()

        for part_no, panel in enumerate(self.cell.panels):
            plotpart = self._get_panel(panel)
            self._insert_attachment_points(panel, plotpart, attachment_points)
            cell_parts.append(plotpart)

            # add marks for
            # - Attachment Points
            # - periodic indicators

        return cell_parts

    def _jojo(self, panel):
        self.x_values = self.cell.rib1.profile_2d.x_values
        self._flatten_cell()
        plotpart = PlotPart(material_code=panel.material_code, name=panel.name)

        cut_allowances = {
            "folded": self.config.allowance_entry_open,
            "parallel": self.config.allowance_trailing_edge,
            "orthogonal": self.config.allowance_design
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

        panel_right = self.outer[1][cut_front.index_right:cut_back.index_right]
        panel_back = cut_back.curve.copy()
        panel_left = self.outer[0][cut_front.index_left:cut_back.index_left:-1]
        panel_front = cut_front.curve.copy()

        plotpart.layers["marks"] += [panel_back, panel_front]

        plotpart.layers["marks"] += [
            PolyLine2D([self.ballooned[0][front_left], self.ballooned[1][front_right]]),
            PolyLine2D([self.ballooned[0][back_left], self.ballooned[1][back_right]])]

        return plotpart

    def _get_panel(self, panel):
        plotpart = PlotPart(material_code=panel.material_code, name=panel.name)

        cut_allowances = {
            "folded": self.config.allowance_entry_open,
            "parallel": self.config.allowance_trailing_edge,
            "orthogonal": self.config.allowance_design
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

        panel_left = self.outer[0][cut_front.index_left:cut_back.index_left]
        panel_back = cut_back.curve.copy()
        panel_right = self.outer[1][cut_front.index_right:cut_back.index_right:-1]
        panel_front = cut_front.curve.copy()

        # spitzer schnitt
        # rechts
        if cut_front.index_right >= cut_back.index_right:
            panel_right = PolyLine2D([])

            _cuts = panel_front.cut_with_polyline(panel_back, startpoint=len(panel_front)-1)
            try:
                ik_front, ik_back = next(_cuts)
                panel_back = panel_back[:ik_back]
                panel_front = panel_front[:ik_front]
            except StopIteration:
                pass  # todo: fix!!

        #lechts
        if cut_front.index_left >= cut_back.index_left:
            panel_left = PolyLine2D([])

            _cuts = panel_front.cut_with_polyline(panel_back, startpoint=0)
            try:
                ik_front, ik_back = next(_cuts)
                panel_back = panel_back[:ik_back]
                panel_front = panel_front[:ik_front]
            except StopIteration:
                pass  # todo: fix aswell!

        panel_back = panel_back[::-1]
        if panel_right:
            panel_right = panel_right[::-1]

        envelope = panel_right + panel_back + panel_left[::-1] + panel_front
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
            plotpart.layers["cuts"].append(envelope.copy())

        self._insert_text(panel, plotpart)

        return plotpart

    def get_point(self, x):
        ik = get_x_value(self.x_values, x)
        return [lst[ik] for lst in self.ballooned]

    def get_p1_p2(self, x, which):
        which = {"left": 0, "right": 1}[which]
        ik = get_x_value(self.x_values, x)

        return self.ballooned[which][ik], self.outer_orig[which][ik]

    def _insert_text(self, panel, plotpart):
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

    def _insert_attachment_points(self, panel, plotpart, attachment_points):
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

                if self.config.insert_attachment_point_text:
                    plotpart.layers["text"] += Text(" {} ".format(attachment_point.name), left, right,
                                                    size=0.01,  # 1cm
                                                    align=align, valign=-0.5).get_vectors()

                plotpart.layers["marks"] += [PolyLine2D(self.get_p1_p2(attachment_point.rib_pos, which))]

    def get_dribs(self):
        dribs = []
        for drib in self.cell.diagonals:
            dribs.append(self._get_drib(drib))

        return dribs

    def _get_drib(self, d_rib):
        plotpart = PlotPart(material_code=d_rib.material_code, name=d_rib.name)
        left, right = d_rib.get_flattened(self.cell)
        left_out = left.copy()
        right_out = right.copy()

        left_out.add_stuff(-self.config.allowance_general)
        right_out.add_stuff(self.config.allowance_general)

        if self.config.allowance_drib_num_folds > 0:
            alw2 = self.config.allowance_drib_folds
            cut_front = cuts["folded"]([[left, 0], [right, 0]],
                                       left_out,
                                       right_out,
                                       -alw2,
                                       num_folds=1)
            cut_back = cuts["folded"]([[left, len(left) - 1],
                                       [right, len(right) - 1]],
                                      left_out,
                                      right_out,
                                      alw2,
                                      num_folds=1)

        else:
            raise NotImplementedError

        # print("left", left_out[cut_front[1]:cut_back[1]].get_length())
        plotpart.layers["cuts"] += [left_out[cut_front.index_left:cut_back.index_left] +
                                    cut_back.curve +
                                    right_out[cut_front.index_right:cut_back.index_right:-1] +
                                    cut_front.curve[::-1]]

        plotpart.layers["marks"].append(PolyLine2D([left[0], right[0]]))
        plotpart.layers["marks"].append(PolyLine2D([left[len(left)-1], right[len(right)-1]]))

        #print(left, right)

        plotpart.layers["stitches"] += [left, right]
        #print(left[0], right[0])
        #plotpart.stitches.append(left)

        plotpart.layers["text"] += Text(" {} ".format(d_rib.name), left[0], right[0], valign=0.6).get_vectors()

        return plotpart