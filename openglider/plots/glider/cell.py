import collections

from openglider.airfoil import get_x_value
import openglider.plots
from openglider.vector.text import get_text_vector
from openglider.plots import sewing_config, cuts, PlotPart
from openglider.vector import PolyLine2D


def flattened_cell(cell):
    # assert isinstance(cell, Cell)
    left, right = openglider.plots.projection.flatten_list(cell.prof1, cell.prof2)
    left_bal = left.copy()
    right_bal = right.copy()
    ballooning = [cell.ballooning[x] for x in cell.rib1.profile_2d.x_values]
    for i in range(len(left)):
        diff = right[i] - left[i]
        left_bal.data[i] -= diff * ballooning[i]
        right_bal.data[i] += diff * ballooning[i]
    return left_bal, left, right, right_bal


def get_panels(glider):
    panels = collections.OrderedDict()
    xvalues = glider.profile_x_values

    for cell_no, cell in enumerate(glider.cells):
        cell_parts = []
        left_bal, left, right, right_bal = flattened_cell(cell)
        left_out = left_bal.copy()
        right_out = right_bal.copy()
        left_out.add_stuff(-sewing_config["allowance"]["general"])
        right_out.add_stuff(sewing_config["allowance"]["general"])
        left_out.check()
        right_out.check()
        for part_no, panel in enumerate(cell.panels):
            front_left = get_x_value(xvalues, panel.cut_front["left"])
            back_left = get_x_value(xvalues, panel.cut_back["left"])
            front_right = get_x_value(xvalues, panel.cut_front["right"])
            back_right = get_x_value(xvalues, panel.cut_back["right"])

            amount_front = -panel.cut_front.get("amount", sewing_config["allowance"][panel.cut_front["type"]])
            amount_back = panel.cut_back.get("amount", sewing_config["allowance"][panel.cut_back["type"]])

            cut_front = cuts[panel.cut_front["type"]]([[left_bal, front_left],
                                                       [right_bal, front_right]],
                                                      left_out, right_out, amount_front)
            cut_back = cuts[panel.cut_back["type"]]([[left_bal, back_left],
                                                     [right_bal, back_right]],
                                                    left_out, right_out, amount_back)

            # spitzer schnitt
            # links
            if cut_front[1] >= cut_back[1]:
                cut_front_new = PolyLine2D(cut_front[0])
                ik1, ik2 = cut_front_new.cut_with_polyline(cut_back[0], startpoint=0)
                panel_cut = PolyLine2D(cut_back[0])[ik2:]
                panel_cut += right_out[cut_front[2]:cut_back[2]:-1]
                panel_cut += cut_front_new[ik1::-1]
            # rechts
            elif cut_front[2] >= cut_back[2]:
                cut_front_new = PolyLine2D(cut_front[0])
                ik1, ik2 = cut_front_new.cut_with_polyline(cut_back[0], startpoint=len(cut_front_new)-1)
                panel_cut = left_out[cut_front[2]:cut_back[2]]
                panel_cut += PolyLine2D(cut_back[0])[:ik2]
                panel_cut += cut_front_new[:ik1:-1]

            else:
                panel_cut = left_out[cut_front[1]:cut_back[1]]
                panel_cut += PolyLine2D(cut_back[0])
                panel_cut += right_out[cut_front[2]:cut_back[2]:-1]
                panel_cut += PolyLine2D(cut_front[0])[::-1]

            panel_cut += PolyLine2D([panel_cut[0]])

            part_marks = [left_bal[front_left:back_left] +
                          right_bal[front_right:back_right:-1] +
                          PolyLine2D([left_bal[front_left]])]

            part_name = "cell_{}_part{}".format(cell_no, part_no+1)
            part_text = get_text_vector(" "+part_name+" ",
                                        left_bal[front_left],
                                        right_bal[front_right],
                                        height=0.8)

            # add marks for
            # - Attachment Points
            # - periodic indicators




            cell_parts.append(PlotPart({"CUTS": [panel_cut],
                                        "MARKS": part_marks,
                                        "TEXT": part_text
                                        },
                                       name=part_name))
        panels[cell] = cell_parts

    return panels