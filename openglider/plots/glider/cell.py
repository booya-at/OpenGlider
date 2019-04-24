import math

from openglider.airfoil import get_x_value
from openglider.plots import cuts, PlotPart
from openglider.plots.glider.config import PatternConfig
from openglider.vector import PolyLine2D, vector_angle
from openglider.vector.text import Text
import openglider.vector.projection as projection
from openglider.plots import Layout
from openglider.vector import normalize, norm


class PanelPlot(object):
    DefaultConf = PatternConfig

    def __init__(self, panel, cell, flattended_cell, config):
        self.panel = panel
        self.cell = cell
        self.config = self.DefaultConf(config)

        self.inner, self.ballooned, self.outer, self.outer_orig = flattended_cell
        self.x_values = self.cell.rib1.profile_2d.x_values

    def flatten(self, attachment_points):
        plotpart = PlotPart(material_code=self.panel.material_code, name=self.panel.name)

        cut_allowances = {
            "folded": self.config.allowance_entry_open,
            "parallel": self.config.allowance_trailing_edge,
            "orthogonal": self.config.allowance_design,
            "singleskin": self.config.allowance_entry_open
        }

        cut_types = {
            "folded": self.config.cut_entry,
            "parallel": self.config.cut_trailing_edge,
            "orthogonal": self.config.cut_design,
            "singleskin": self.config.cut_entry
        }

        front_left = get_x_value(self.x_values, self.panel.cut_front["left"])
        back_left = get_x_value(self.x_values, self.panel.cut_back["left"])
        front_right = get_x_value(self.x_values, self.panel.cut_front["right"])
        back_right = get_x_value(self.x_values, self.panel.cut_back["right"])

        # allowance fallbacks
        allowance_front = cut_allowances[self.panel.cut_front["type"]]
        allowance_back = cut_allowances[self.panel.cut_back["type"]]

        # get allowance from self.panel
        amount_front = -self.panel.cut_front.get("amount", allowance_front)
        amount_back = self.panel.cut_back.get("amount", allowance_back)

        # cuts -> cut-line, index left, index right
        cut_front = cut_types[self.panel.cut_front["type"]](amount_front)
        cut_back = cut_types[self.panel.cut_back["type"]](amount_back)

        cut_front_result = cut_front.apply([[self.ballooned[0], front_left],
                                            [self.ballooned[1], front_right]],
                                           self.outer[0], self.outer[1])

        cut_back_result = cut_back.apply([[self.ballooned[0], back_left],
                                [self.ballooned[1], back_right]],
                               self.outer[0], self.outer[1])

        panel_left = self.outer[0][cut_front_result.index_left:cut_back_result.index_left]
        panel_back = cut_back_result.curve.copy()
        panel_right = self.outer[1][cut_front_result.index_right:cut_back_result.index_right:-1]
        panel_front = cut_front_result.curve.copy()

        # spitzer schnitt
        # rechts
        if cut_front_result.index_right >= cut_back_result.index_right:
            panel_right = PolyLine2D([])

            _cuts = panel_front.cut_with_polyline(panel_back, startpoint=len(panel_front) - 1)
            try:
                ik_front, ik_back = next(_cuts)
                panel_back = panel_back[:ik_back]
                panel_front = panel_front[:ik_front]
            except StopIteration:
                pass  # todo: fix!!

        # lechts
        if cut_front_result.index_left >= cut_back_result.index_left:
            panel_left = PolyLine2D([])

            _cuts = panel_front.cut_with_polyline(panel_back, startpoint=0)
            try:
                ik_front, ik_back = next(_cuts)
                panel_back = panel_back[ik_back:]
                panel_front = panel_front[ik_front:]
            except StopIteration:
                pass  # todo: fix aswell!

        panel_back = panel_back[::-1]
        if panel_right:
            panel_right = panel_right[::-1]

        #print(panel_left)

        envelope = panel_right + panel_back
        if len(panel_left) > 0:
            envelope += panel_left[::-1]
        envelope += panel_front
        envelope += PolyLine2D([envelope[0]])

        plotpart.layers["envelope"].append(envelope)

        # sewings
        plotpart.layers["stitches"] += [
            self.ballooned[0][front_left:back_left],
            self.ballooned[1][front_right:back_right]]

        # folding line
        plotpart.layers["marks"] += [
            PolyLine2D([self.ballooned[0][front_left], self.ballooned[1][front_right]]),
            PolyLine2D([self.ballooned[0][back_left], self.ballooned[1][back_right]])]

        # TODO
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

        self._insert_text(plotpart)
        self._insert_controlpoints(plotpart)
        self._insert_attachment_points(plotpart, attachment_points=attachment_points)
        self._insert_diagonals(plotpart)
        # self._insert_center_rods(plotpart)
        # TODO: add in parametric way

        self._align_upright(plotpart)

        return plotpart

    def get_point(self, x):
        ik = get_x_value(self.x_values, x)
        return [lst[ik] for lst in self.ballooned]

    def get_p1_p2(self, x, which):
        side = {"left": 0, "right": 1}[which]
        ik = get_x_value(self.x_values, x)

        return self.ballooned[side][ik], self.outer_orig[side][ik]

    def _align_upright(self, plotpart):
        def get_p1_p2(side):
            p1 = self.get_p1_p2(self.panel.cut_front[side], side)[0]
            p2 = self.get_p1_p2(self.panel.cut_back[side], side)[0]

            return p2 - p1

        vector = get_p1_p2("left")
        vector += get_p1_p2("right")
        angle = vector_angle(vector, [0, 1])

        plotpart.rotate(angle)
        return plotpart

    def _insert_text(self, plotpart):
        if self.config.layout_seperate_panels and not self.panel.is_lower():
            left = get_x_value(self.x_values, self.panel.cut_back["left"])
            right = get_x_value(self.x_values, self.panel.cut_back["right"])
            p2 = self.ballooned[1][right]
            p1 = self.ballooned[0][left]
            align = "left"
        else:
            left = get_x_value(self.x_values, self.panel.cut_front["left"])
            right = get_x_value(self.x_values, self.panel.cut_front["right"])
            p1 = self.ballooned[1][right]
            p2 = self.ballooned[0][left]
            align = "right"
        text = self.panel.name
        part_text = Text(text, p1, p2,
                         size=self.config.allowance_design * 0.8,
                         align=align,
                         valign=0.6,
                         height=0.8).get_vectors()
        plotpart.layers["text"] += part_text

    def _insert_controlpoints(self, plotpart):
        for x in self.config.distribution_controlpoints:
            for side in ("left", "right"):
                if self.panel.cut_front[side] <= x <= self.panel.cut_back[side]:
                    p1, p2 = self.get_p1_p2(x, side)
                    plotpart.layers["L0"] += self.config.marks_laser_controlpoint(p1, p2)

    def _insert_diagonals(self, plotpart):
        def insert_diagonal(x, height, side, front):
            if height == 1:
                xval = -x
            elif height == -1:
                xval = x
            else:
                return

            if self.panel.cut_front[side] <= xval <= self.panel.cut_back[side]:
                p1, p2 = self.get_p1_p2(xval, side)
                plotpart.layers["L0"] += self.config.marks_laser_diagonal(p1, p2)
                if (front and height == -1) or (not front and height == 1):
                    plotpart.layers["marks"] += self.config.marks_diagonal_front(p1, p2)
                else:
                    plotpart.layers["marks"] += self.config.marks_diagonal_back(p1, p2)

        for strap in self.cell.straps + self.cell.diagonals:
            insert_diagonal(*strap.left_front, side="left", front=False)
            insert_diagonal(*strap.left_back, side="left", front=True)
            insert_diagonal(*strap.right_front, side="right", front=True)
            insert_diagonal(*strap.right_back, side="right", front=False)

    def _insert_attachment_points(self, plotpart, attachment_points):
        for attachment_point in attachment_points:
            if hasattr(attachment_point, "cell"):
                if attachment_point.cell != self.cell:
                    continue

                cell_pos = attachment_point.cell_pos

            elif hasattr(attachment_point, "rib"):

                if attachment_point.rib not in self.cell.ribs:
                    continue


                if attachment_point.rib == self.cell.rib1:
                    cell_pos = 0
                    align = ("left", "right")
                elif attachment_point.rib == self.cell.rib2:
                    cell_pos = 1

            cut_f_l = self.panel.cut_front["left"]
            cut_f_r = self.panel.cut_front["right"]
            cut_b_l = self.panel.cut_back["left"]
            cut_b_r = self.panel.cut_back["right"]
            cut_f = cut_f_l + cell_pos * (cut_f_r - cut_f_l)
            cut_b = cut_b_l + cell_pos * (cut_b_r - cut_b_l)

            if cut_f <= attachment_point.rib_pos <= cut_b:
                rib_pos = attachment_point.rib_pos
                left, right = self.get_point(rib_pos)

                p1 = left + cell_pos * (right - left)
                d = normalize(right - left) * 0.008  # 8mm
                if cell_pos == 1:
                    p2 = p1 + d
                else:
                    p2 = p1 - d
                #p1, p2 = self.get_p1_p2(attachment_point.rib_pos, which)
                plotpart.layers["marks"] += self.config.marks_attachment_point(p1, p2)
                plotpart.layers["L0"] += self.config.marks_laser_attachment_point(p1, p2)

                if self.config.insert_attachment_point_text:
                    text_align = "left" if cell_pos > 0.7 else "right"

                    if text_align == "right":
                        d1 = norm(self.get_point(cut_f_l)[0] - left)
                        d2 = norm(self.get_point(cut_b_l)[0] - left)
                    else:
                        d1 = norm(self.get_point(cut_f_r)[1] - right)
                        d2 = norm(self.get_point(cut_b_r)[1] - right)

                    bl = self.ballooned[0]
                    br = self.ballooned[1]

                    text_height = 0.01 * 0.8
                    dmin = text_height + 0.001

                    if d1 < dmin and d2 + d1 > 2*dmin:
                        offset = dmin - d1
                        ik = get_x_value(self.x_values, rib_pos)
                        left = bl[bl.extend(ik, offset)]
                        right = br[br.extend(ik, offset)]
                    elif d2 < dmin and d1 + d2 > 2*dmin:
                        offset = dmin - d2
                        ik = get_x_value(self.x_values, rib_pos)
                        left = bl[bl.extend(ik, -offset)]
                        right = br[br.extend(ik, -offset)]

                    if self.config.layout_seperate_panels and self.panel.is_lower:
                        # rotated later
                        p2 = left
                        p1 = right
                        text_align = text_align
                    else:
                        p1 = left
                        p2 = right
                        text_align = text_align
                    plotpart.layers["text"] += Text(" {} ".format(attachment_point.name), p1, p2,
                                                    size=0.01,  # 1cm
                                                    align=text_align, valign=0, height=0.8).get_vectors()

    def _get_middle_line(self, x=0.5):
        line = []

        for left, right in zip(*self.ballooned):
            line.append(left + x * (right-left))

        return PolyLine2D(line)

    def _insert_center_rods(self, plotpart):
        start = -0.15
        end = 0.15

        front = (self.panel.cut_front["left"] + self.panel.cut_front["right"]) / 2
        back = (self.panel.cut_back["left"] + self.panel.cut_back["right"]) / 2

        if end < min(self.panel.cut_front["left"], self.panel.cut_front["right"]):
            return
        elif start > max(self.panel.cut_back["left"], self.panel.cut_back["right"]):
            return

        k_start = get_x_value(self.x_values, start)
        k_end = get_x_value(self.x_values, end)

        middle_line = self._get_middle_line(0.5)

        curve_left = self.ballooned[0]
        curve_right = self.ballooned[1]

        # cut with front and back
        front_left = curve_left[get_x_value(self.x_values, self.panel.cut_front["left"])]
        front_right = curve_right[get_x_value(self.x_values, self.panel.cut_front["right"])]
        back_left = curve_left[get_x_value(self.x_values, self.panel.cut_back["left"])]
        back_right = curve_right[get_x_value(self.x_values, self.panel.cut_back["right"])]

        cut_fronts = middle_line.cut(front_left, front_right, startpoint=k_start, extrapolate=True)
        cut_backs = middle_line.cut(back_left, back_right, startpoint=k_end, extrapolate=True)

        cut_front = next(cut_fronts)[0]
        cut_back = next(cut_backs)[0]

        k_front = max(k_start, cut_front)
        k_back = min(k_end, cut_back)

        #print(cut_front, k_front, cut_back, k_back, self.panel.cut_front, self.panel.cut_back)

        if k_back > k_front:

            plotpart.layers["marks"] += [middle_line[k_front:k_back]]

            if front < start < back:
                k_start = get_x_value(self.x_values, start)
                plotpart.layers["L0"].append(PolyLine2D([middle_line[k_start]]))

            if front < end < back:
                k_end = get_x_value(self.x_values, end)
                plotpart.layers["L0"].append(PolyLine2D([middle_line[k_end]]))


class DribPlot(object):
    DefaultConf = PatternConfig

    def __init__(self, drib, cell, config):
        self.drib = drib
        self.cell = cell
        self.config = self.DefaultConf(config)

        self._left, self._right = None, None
        self._left_out = self._right_out = None

    def _get_inner(self):
        if self._left is None:
            left, right = self.drib.get_flattened(self.cell)
            self._left = left
            self._right = right
        return self._left, self._right

    def _get_outer(self):
        if self._left_out is None:
            left, right = self._get_inner()
            left_out = left.copy()
            right_out = right.copy()

            left_out.add_stuff(-self.config.allowance_general)
            right_out.add_stuff(self.config.allowance_general)
            self._left_out = left_out
            self._right_out = right_out

        return self._left_out, self._right_out

    def get_left(self, x):
        return self.get_p1_p2(x, side=0)

    def get_right(self, x):
        return self.get_p1_p2(x, side=1)

    def _is_valid(self, x, side=0):
        if side == 0:
            front = self.drib.left_front
            back = self.drib.left_back
        else:
            front = self.drib.right_front
            back = self.drib.right_back

        if (front[1], back[1]) not in ((-1, -1), (1, 1)):
            return False

        if front[1] > 0:
            # swapped sides
            boundary = [-front[0], -back[0]]
        else:
            boundary = [front[0], back[0]]
        boundary.sort()

        if not boundary[0] <= x <= boundary[1]:
            return False

        return True

    def get_p1_p2(self, x, side=0):
        assert self._is_valid(x, side=side)

        left, right = self._get_inner()
        left_out, right_out = self._get_outer()

        if side == 0:
            front = self.drib.left_front
            back = self.drib.left_back
            rib = self.cell.rib1
            inner = left
            outer = left_out
        else:
            front = self.drib.right_front
            back = self.drib.right_back
            rib = self.cell.rib2
            inner = right
            outer = right_out

        assert front[0] <= x <= back[0]

        foil = rib.profile_2d
        # -1 -> lower, 1 -> upper
        foil_side = 1 if front[1] == -1 else -1

        x1 = front[0] * foil_side
        x2 = x * foil_side

        ik_1 = foil(x1)
        ik_2 = foil(x2)
        length = foil[ik_1:ik_2].get_length() * rib.chord

        ik_new = inner.extend(0, length)
        return inner[ik_new], outer[ik_new]

    def _insert_attachment_points(self, plotpart, attachment_points=None):
        attachment_points = attachment_points or []

        for attachment_point in attachment_points:
            if not hasattr(attachment_point, "rib"):
                continue
            x = attachment_point.rib_pos
            if attachment_point.rib is self.cell.rib1:
                if not self._is_valid(x, side=0):
                    continue
                p1, p2 = self.get_left(attachment_point.rib_pos)
            elif attachment_point.rib is self.cell.rib2:
                if not self._is_valid(x, side=1):
                    continue

                p1, p2 = self.get_right(attachment_point.rib_pos)
            else:
                continue

            plotpart.layers["marks"] += self.config.marks_attachment_point(p1, p2)
            plotpart.layers["L0"] += self.config.marks_laser_attachment_point(p1, p2)

    def _insert_text(self, plotpart):
        left, right = self._get_inner()

        # text_p1 = left_out[0] + self.config.drib_text_position * (right_out[0] - left_out[0])
        text_p1 = left[0]
        plotpart.layers["text"] += Text(" {} ".format(self.drib.name),
                                        text_p1,
                                        right[0],
                                        size=self.config.drib_allowance_folds * 0.8,
                                        height=0.8,
                                        valign=0.6).get_vectors()

    def flatten(self, attachment_points=None):
        return self._flatten(attachment_points, self.config.drib_num_folds)

    def _flatten(self, attachment_points, num_folds):
        plotpart = PlotPart(material_code=self.drib.material_code, name=self.drib.name)
        left, right = self._get_inner()
        left_out, right_out = self._get_outer()

        if num_folds > 0:
            alw2 = self.config.drib_allowance_folds
            cut_front = self.config.cut_diagonal_fold(-alw2, num_folds=num_folds)
            cut_back = self.config.cut_diagonal_fold(alw2, num_folds=num_folds)
            cut_front_result = cut_front.apply([[left, 0], [right, 0]], left_out, right_out)
            cut_back_result = cut_back.apply([[left, len(left) - 1], [right, len(right) - 1]], left_out, right_out)

            plotpart.layers["cuts"] += [left_out[cut_front_result.index_left:cut_back_result.index_left] +
                                        cut_back_result.curve +
                                        right_out[cut_front_result.index_right:cut_back_result.index_right:-1] +
                                        cut_front_result.curve[::-1]]

        else:
            p1 = next(left_out.cut(left[0], right[0], startpoint=0, extrapolate=True))[0]
            p2 = next(left_out.cut(left[len(left)-1], right[len(right)-1], startpoint=len(left_out), extrapolate=True))[0]
            p3 = next(right_out.cut(left[0], right[0], startpoint=0, extrapolate=True))[0]
            p4 = next(right_out.cut(left[len(left)-1], right[len(right)-1], startpoint=len(right_out), extrapolate=True))[0]

            outer = left_out[p1:p2]
            outer += right_out[p3:p4][::-1]
            outer += PolyLine2D([left_out[p1]])
            plotpart.layers["cuts"].append(outer)

        # print("left", left_out[cut_front[1]:cut_back[1]].get_length())

        plotpart.layers["marks"].append(PolyLine2D([left[0], right[0]]))
        plotpart.layers["marks"].append(PolyLine2D([left[len(left) - 1], right[len(right) - 1]]))

        # print(left, right)

        plotpart.layers["stitches"] += [left, right]

        self._insert_attachment_points(plotpart, attachment_points)
        self._insert_text(plotpart)

        return plotpart


class StrapPlot(DribPlot):
    def flatten(self, attachment_points=None):
        return self._flatten(attachment_points, self.config.strap_num_folds)


class CellPlotMaker:
    DefaultConf = PatternConfig

    def __init__(self, cell, attachment_points, config=None):
        self.cell = cell
        self.attachment_points = attachment_points
        self.config = self.DefaultConf(config)

        self._flattened_cell = None

    def _get_flatten_cell(self):
        if self._flattened_cell is None:
            # assert isinstance(cell, Cell)
            left, right = projection.flatten_list(self.cell.prof1,
                                                  self.cell.prof2)
            left_bal = left.copy()
            right_bal = right.copy()
            ballooning = [self.cell.ballooning[x] for x in self.cell.rib1.profile_2d.x_values]
            for i in range(len(left)):
                diff = (right[i] - left[i]) * ballooning[i] / 2
                left_bal.data[i] -= diff
                right_bal.data[i] += diff

            inner = [left, right]
            ballooned = [left_bal, right_bal]

            outer_left = left_bal.copy().add_stuff(-self.config.allowance_general)
            outer_right = right_bal.copy().add_stuff(self.config.allowance_general)

            outer_orig = [outer_left, outer_right]
            outer = [l.copy().check() for l in outer_orig]

            self._flattened_cell = [
                inner,
                ballooned,
                outer,
                outer_orig
            ]

        return self._flattened_cell

    def get_panels(self, panels=None):
        cell_panels = []
        flattened_cell = self._get_flatten_cell()

        if panels is None:
            panels = self.cell.panels

        for part_no, panel in enumerate(panels):
            plot = PanelPlot(panel, self.cell, flattened_cell, self.config)
            dwg = plot.flatten(self.attachment_points)
            cell_panels.append(dwg)

        return Layout.stack_column(cell_panels, self.config.patterns_align_dist_y)

    def get_panels_lower(self):
        panels = [p for p in self.cell.panels if p.is_lower()]
        layout = self.get_panels(panels)
        return layout

    def get_panels_upper(self):
        panels = [p for p in self.cell.panels if not p.is_lower()]
        layout = self.get_panels(panels)
        return layout

    def get_dribs(self):
        dribs = []
        for drib in self.cell.diagonals:
            drib_plot = DribPlot(drib, self.cell, self.config)
            dribs.append(drib_plot.flatten(self.attachment_points))

        return Layout.stack_column(dribs, self.config.patterns_align_dist_y)

    def get_straps(self):
        straps = []
        for strap in self.cell.straps:
            plot = StrapPlot(strap, self.cell, self.config)
            straps.append(plot.flatten(self.attachment_points))

        return Layout.stack_column(straps, self.config.patterns_align_dist_y)
