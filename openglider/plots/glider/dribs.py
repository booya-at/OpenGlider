from openglider.plots import sewing_config, cuts, PlotPart
from openglider.vector import PolyLine2D
from openglider.vector.text import get_text_vector


def get_dribs(glider):
    dribs = []
    for cell_no, cell in enumerate(glider.cells):
        cell_dribs = []
        for d_no, d_rib in enumerate(cell.diagonals):
            left, right = d_rib.get_flattened(cell)
            left_out = left.copy()
            right_out = right.copy()
            alw = sewing_config["allowance"]["general"]
            alw2 = sewing_config["allowance"]["diagonals"]
            left_out.add_stuff(-alw)
            right_out.add_stuff(alw)

            cut_front = cuts["parallel"]([[left, 0],
                                          [right, 0]],
                                         left_out, right_out, -alw2)
            cut_back = cuts["parallel"]([[left, len(left)-1],
                                         [right, len(right)-1]],
                                        left_out, right_out, alw2)

            #print("left", left_out[cut_front[1]:cut_back[1]].get_length())
            part_cuts = [left_out[cut_front[1]:cut_back[1]] +
                         PolyLine2D(cut_back[0]) +
                         right_out[cut_front[2]:cut_back[2]:-1] +
                         PolyLine2D(cut_front[0])[::-1]]
            part_marks = [left + right[::-1] +
                          PolyLine2D([left[0]])]

            d_rib_name = "cell_{}_drib_{}".format(cell_no, d_no)
            text = get_text_vector(" "+d_rib_name+" ",
                                   left[0], right[0])

            cell_dribs.append(PlotPart({"CUTS": part_cuts,
                                        "MARKS": part_marks,
                                        "TEXT": text},
                                       name=d_rib_name))

        dribs.append(cell_dribs)

    return dribs
