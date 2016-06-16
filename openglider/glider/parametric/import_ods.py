from __future__ import division

import numbers
import ezodf
import numpy

from openglider.airfoil import BezierProfile2D, Profile2D
from openglider.vector.spline import Bezier, SymmetricBezier
from openglider.vector import Interpolation

from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.lines import UpperNode2D, LowerNode2D, BatchNode2D, Line2D, LineSet2D
from openglider.glider.rib import MiniRib
from openglider.glider.ballooning import BallooningBezier


element_keywords = {
    "cuts": ["cells", "left", "right", "type"],
    "a": "",
}


def import_ods_2d(Glider2D, filename, numpoints=4, calc_lineset_nodes=False):
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets

    cell_sheet = sheets[1]
    rib_sheet = sheets[2]

    # file-version
    if cell_sheet[0, 0].value == "V2" or cell_sheet[0, 0].value == "V2":
        file_version = 2
    else:
        file_version = 1
    # ------------

    # profiles = [BezierProfile2D(profile) for profile in transpose_columns(sheets[3])]
    profiles = [Profile2D(profile, name) for name, profile in transpose_columns(sheets[3])]

    try:
        geometry = get_geometry_parametric(sheets[5])
    except Exception:
        geometry = get_geometry_explicit(sheets[0])

    balloonings = []
    for name, baloon in transpose_columns(sheets[4]):
        if baloon:
            i = 0
            while baloon[i+1][0] > baloon[i][0]:
                i += 1

            upper = baloon[:i+1]
            lower = baloon[i+1:]

            balloonings.append(BallooningBezier(upper, lower, name=name))

    data = {}
    datasheet = sheets[-1]
    assert isinstance(datasheet, ezodf.Sheet)
    for row in datasheet.rows():
        if len(row) > 1:
            data[row[0].value] = row[1].value


    # Attachment points: rib_no, id, pos, force
    attachment_points = get_attachment_points(rib_sheet)
    attachment_points_lower = get_lower_aufhaengepunkte(data)

    # RIB HOLES
    rib_hole_keywords = ["ribs", "pos", "size"]
    rib_holes = read_elements(rib_sheet, "QUERLOCH", len_data=2)
    rib_holes = to_dct(rib_holes, rib_hole_keywords)
    rib_holes = group(rib_holes, "ribs")

    rigidfoil_keywords = ["ribs", "start", "end", "distance"]
    rigidfoils = read_elements(rib_sheet, "RIGIDFOIL", len_data=3)
    rigidfoils = to_dct(rigidfoils, rigidfoil_keywords)
    rigidfoils = group(rigidfoils, "ribs")

    # CUTS
    def get_cuts(names, target_name):
        objs = []
        for name_src in names:
            objs += read_elements(cell_sheet, name_src, len_data=2)

        cuts_this = [{"cells": cut[0], "left": float(cut[1]), "right": float(cut[2]), "type": target_name} for cut in objs]

        return group(cuts_this, "cells")

    cuts = get_cuts(["EKV", "EKH", "folded"], "folded")
    cuts += get_cuts(["DESIGNM", "DESIGNO", "orthogonal"], "orthogonal")

    # Diagonals: center_left, center_right, width_l, width_r, height_l, height_r
    diagonals = []
    for res in read_elements(cell_sheet, "QR", len_data=6):
        height1 = res[5]
        height2 = res[6]

        # migration
        if file_version == 1:
            # height (0,1) -> (-1,1)
            height1 = height1 * 2 - 1
            height2 = height2 * 2 - 1
        # ---------

        diagonals.append({"left_front": (res[1] - res[3] / 2, height1),
                          "left_back": (res[1] + res[3] / 2, height1),
                          "right_front": (res[2] - res[4] / 2, height2),
                          "right_back": (res[2] + res[4] / 2, height2),
                          "cells": res[0]})

    for res in read_elements(cell_sheet, "STRAP", len_data=3):
        # [cell_no, x_left, x_right, width]
        diagonals.append({"left_front": (res[1] - res[3]/2, -1),
                          "left_back": (res[1] + res[3]/2, -1),
                          "right_front": (res[2] - res[3]/2, -1),
                          "right_back": (res[2] + res[3]/2, -1),
                          "cells": res[0]
                          })

    diagonals = group(diagonals, "cells")



    straps = []
    straps_keywords = ["cells", "left", "right"]
    for res in read_elements(cell_sheet, "VEKTLAENGE", len_data=2):
        straps.append(zip(straps_keywords, res))
    straps = group(straps, "cells")
    materials = get_material_codes(cell_sheet)

    # minirib -> y, start (x)
    miniribs = []
    for minirib in read_elements(cell_sheet, "MINIRIB", len_data=2):
        miniribs.append({
            "yvalue": minirib[1],
            "front_cut": minirib[2],
            "cells": minirib[0]
        })
    miniribs = group(miniribs, "cells")

    glider_2d = Glider2D(elements={"cuts": cuts,
                                   "holes": rib_holes,
                                   "diagonals": diagonals,
                                   "rigidfoils": rigidfoils,
                                   "straps": straps,
                                   "materials": materials,
                                   "miniribs": miniribs},
                         profiles=profiles,
                         balloonings=balloonings,
                         lineset=tolist_lines(sheets[6], attachment_points_lower, attachment_points),
                         speed=data["SPEED"],
                         glide=data["GLIDE"],
                         **geometry)

    if calc_lineset_nodes:
        glider_3d = glider_2d.get_glider_3d()
        glider_2d.lineset.set_default_nodes2d_pos(glider_3d)
    return glider_2d


def get_geometry_explicit(sheet):
    # All Lists
    front = []
    back = []
    cell_distribution = []
    aoa = []
    arc = []
    profile_merge = []
    ballooning_merge = []
    zrot = []

    y = z = span_last = alpha = 0.
    for i in range(1, sheet.nrows()):
        line = [sheet.get_cell([i, j]).value for j in range(sheet.ncols())]
        if not line[0]:
            break  # skip empty line
        if not all(isinstance(c, numbers.Number) for c in line[:10]):
            raise ValueError("Invalid row ({}): {}".format(i, line))
        # Index, Choord, Span(x_2d), Front(y_2d=x_3d), d_alpha(next), aoa,
        chord = line[1]
        span = line[2]
        x = line[3]
        y += numpy.cos(alpha) * (span - span_last)
        z -= numpy.sin(alpha) * (span - span_last)

        alpha += line[4] * numpy.pi / 180  # angle after the rib

        aoa.append([span, line[5] * numpy.pi / 180])
        arc.append([y, z])
        front.append([span, -x])
        back.append([span, -x - chord])
        cell_distribution.append([span, i - 1])

        profile_merge.append([span, line[8]])
        ballooning_merge.append([span, line[9]])

        zrot.append([span, line[7] * numpy.pi / 180])

        span_last = span


    def symmetric_fit(data):
        not_from_center = data[0][0] == 0
        mirrored = [[-p[0], p[1]] for p in data[not_from_center:]][::-1] + data
        return SymmetricBezier.fit(mirrored)


    has_center_cell = not front[0][0] == 0
    cell_no = (len(front) - 1) * 2 + has_center_cell


    start = (2 - has_center_cell) / cell_no

    const_arr = [0.] + numpy.linspace(start, 1, len(front) - (not has_center_cell)).tolist()
    rib_pos = [0.] + [p[0] for p in front[not has_center_cell:]]
    rib_pos_int = Interpolation(zip(rib_pos, const_arr))
    rib_distribution = [[i, rib_pos_int(i)] for i in numpy.linspace(0, rib_pos[-1], 30)]

    rib_distribution = Bezier.fit(rib_distribution)

    parametric_shape = ParametricShape(symmetric_fit(front), symmetric_fit(back), rib_distribution, cell_no)
    arc_curve = ArcCurve(symmetric_fit(arc))

    return {
        "shape": parametric_shape,
        "arc": arc_curve,
        "aoa": symmetric_fit(aoa),
        "zrot": symmetric_fit(zrot),
        "profile_merge_curve": symmetric_fit(profile_merge),
        "ballooning_merge_curve": symmetric_fit(ballooning_merge)

    }

def get_geometry_parametric(sheet):
    raise NotImplementedError
    # todo -> raise on fail

def get_material_codes(sheet):
    materials = read_elements(sheet, "MATERIAL", len_data=1)
    i = 0
    ret = []
    while materials:
        codes = [el[1] for el in materials if el[0] == i]
        materials = [el for el in materials if el[0] != i]
        ret.append(codes)
        i += 1
    # cell_no, part_no, code
    return ret


def get_attachment_points(sheet, midrib=False):
    # UpperNode2D(rib_no, rib_pos, force, name, layer)
    attachment_points = [UpperNode2D(args[0], args[2], args[3], args[1])
                         for args in read_elements(sheet, "AHP", len_data=3)]
    # attachment_points.sort(key=lambda element: element.nr)

    return {node.name: node for node in attachment_points}
    # return attachment_points


def get_lower_aufhaengepunkte(data):
    aufhaengepunkte = {}
    xyz = {"X": 0, "Y": 1, "Z": 2}
    for key in data:
        if key is not None and "AHP" in key:
            pos = int(key[4])
            aufhaengepunkte.setdefault(pos, [0, 0, 0])
            which = key[3].upper()
            aufhaengepunkte[pos][xyz[which]] = data[key]
    return {nr: LowerNode2D([0, 0], pos, nr)
            for nr, pos in aufhaengepunkte.items()}


def transpose_columns(sheet, columnswidth=2):
    num_columns = sheet.ncols()
    num_elems = num_columns // columnswidth
    # if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(num_elems):
        first_column = col*columnswidth
        last_column = (col+1)*columnswidth
        columns = range(first_column, last_column)
        name = sheet[0, first_column].value
        if not isinstance(name, numbers.Number):  # py2/3: str!=unicode
            start = 1
        else:
            name = "unnamed"
            start = 0

        element = []

        for i in range(start, sheet.nrows()):
            row = [sheet[i, j].value for j in columns]
            if all([j is None for j in row]):  # Break at empty line
                break
            if not all([isinstance(j, numbers.Number) for j in row]):
                raise ValueError("Invalid value at row {}: {}".format(i, row))
            element.append(row)
        result.append((name, element))
    return result


def tolist_lines(sheet, attachment_points_lower, attachment_points_upper):
    # upper -> dct {name: node}
    num_rows = sheet.nrows()
    num_cols = sheet.ncols()
    linelist = []
    current_nodes = [None for row in range(num_cols)]
    row = 0
    column = 0
    count = 0

    while row < num_rows:
        value = sheet.get_cell([row, column]).value  # length or node_no

        if value is not None:
            if column == 0:  # first (line-)floor
                current_nodes = [attachment_points_lower[int(sheet.get_cell([row, 0]).value)]] + \
                                [None for __ in range(num_cols)]
                column += 1

            else:
                # We have a line
                line_type_name = sheet.get_cell([row, column + 1]).value

                lower_node = current_nodes[column // 2]

                # gallery
                if column + 2 >= num_cols-1 or sheet.get_cell([row, column + 2]).value is None:

                    upper = attachment_points_upper[value]
                    line_length = None
                    row += 1
                    column = 0
                # other line
                else:
                    upper = BatchNode2D([0, 0])
                    current_nodes[column // 2 + 1] = upper
                    line_length = sheet.get_cell([row, column]).value
                    column += 2

                linelist.append(
                    Line2D(lower_node, upper, target_length=line_length, line_type=line_type_name))
                count += 1

        else:
            if column == 0:
                column += 1
            elif column + 2 >= num_cols:
                row += 1
                column = 0
            else:
                column += 2

    return LineSet2D(linelist)


def read_elements(sheet, keyword, len_data=2):
    """
    Return rib/cell_no for the element + data

    -> read_elements(sheet, "AHP", 2) -> [ [rib_no, id, x], ...]
    """

    elements = []
    column = 0
    while column < sheet.ncols():
        if sheet.get_cell([0, column]).value == keyword:
            #print("found, ", j, sheet[0, j].value, sheet.ncols(), sheet[1, j].value)
            for row in range(1, sheet.nrows()):
                line = [sheet.get_cell([row, column + k]).value for k in range(len_data)]
                #print(line)
                if line[0] is not None:
                    elements.append([row - 1] + line)
            column += len_data
        else:
            column += 1
    return elements


def to_dct(elems, keywords):
    return [{key: value for key, value in zip(keywords, elem)} for elem in elems]


def group(lst, keyword):
    new_lst = []

    def equal(first, second):
        if first.keys() != second.keys():
            return False
        for key in first:
            if key == keyword:
                continue
            if first[key] != second[key]:
                return False

        return True

    def insert(_obj):
        for obj2 in new_lst:
            if equal(_obj, obj2):
                obj2[keyword] += _obj[keyword]
                return

        # nothing found
        new_lst.append(_obj)

    for obj in lst:
        # create a list to group
        obj[keyword] = [obj[keyword]]
        insert(obj)

    return new_lst
