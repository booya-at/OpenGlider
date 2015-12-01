from openglider.plots import sewing_config, cuts, PlotPart
from openglider.vector import PolyLine2D
from openglider.vector.text import Text


def get_dribs(glider):
    dribs = []
    for cell_no, cell in enumerate(glider.cells):
        cell_dribs = []
        for d_no, d_rib in enumerate(cell.diagonals):
            plotpart = PlotPart(material_code=d_rib.material_code, name=d_rib.name)
            left, right = d_rib.get_flattened(cell)
            left_out = left.copy()
            right_out = right.copy()
            alw = sewing_config["allowance"]["general"]
            alw2 = sewing_config["allowance"]["diagonals"]
            left_out.add_stuff(-alw)
            right_out.add_stuff(alw)

            cut_front = cuts["folded"]([[left, 0],
                                          [right, 0]],
                                         left_out, right_out, -alw2, num_folds=1)
            cut_back = cuts["folded"]([[left, len(left) - 1],
                                         [right, len(right) - 1]],
                                        left_out, right_out, alw2, num_folds=1)

            # print("left", left_out[cut_front[1]:cut_back[1]].get_length())
            plotpart.layers["cuts"] += [left_out[cut_front[1]:cut_back[1]] +
                              PolyLine2D(cut_back[0]) +
                              right_out[cut_front[2]:cut_back[2]:-1] +
                              PolyLine2D(cut_front[0])[::-1]]

            plotpart.layers["marks"].append(PolyLine2D([left[0], right[0]]))
            plotpart.layers["marks"].append(PolyLine2D([left[len(left)-1], right[len(right)-1]]))

            #print(left, right)

            plotpart.layers["stitches"] += [left, right]
            #print(left[0], right[0])
            #plotpart.stitches.append(left)

            plotpart.layers["text"] += Text(" {} ".format(d_rib.name), left[0], right[0], valign=0.6).get_vectors()

            cell_dribs.append(plotpart)

        dribs.append(cell_dribs)

    return dribs
