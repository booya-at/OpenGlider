from __future__ import division

import numbers
import re

import ezodf
import numpy as np
import logging
import typing
import euklid

from openglider.airfoil import BezierProfile2D, Profile2D

from openglider.glider.parametric.arc import ArcCurve
from openglider.glider.parametric.shape import ParametricShape
from openglider.glider.parametric.lines import UpperNode2D, LowerNode2D, BatchNode2D, Line2D, LineSet2D
from openglider.glider.rib import MiniRib
from openglider.glider.ballooning import BallooningBezier, BallooningBezierNeu
from openglider.utils.table import Table
from openglider.materials import cloth
from openglider.glider.parametric.table.holes import HolesTable
from openglider.glider.parametric.table.diagonals import DiagonalTable, StrapTable
from openglider.glider.parametric.table.ballooning import BallooningTable
from openglider.glider.parametric.table.ribs_singleskin import SingleSkinTable


logger = logging.getLogger(__name__)
element_keywords = {
    "cuts": ["cells", "left", "right", "type"],
    "a": "",
}

def filter_elements_from_table(table: Table, key: str, length: int):
    new_table = Table()
    for column in range(table.num_columns):
        if table[0, column] == key:
            new_table.append_right(table.get_columns(column, column+length))
    
    return new_table

def import_ods_2d(Glider2D, filename, numpoints=4, calc_lineset_nodes=False):
    logger.info(f"Import file: {filename}")
    ods = ezodf.opendoc(filename)
    sheets = ods.sheets
    tables = Table.load(filename)

    cell_sheet = tables[1]
    rib_sheet = tables[2]

    # file-version
    file_version_match = re.match(r"V([0-9]*)", str(cell_sheet["A1"]))
    if file_version_match:
        file_version = int(file_version_match.group(1))
    else:
        file_version = 1
    logger.info(f"Loading file version {file_version}")
    # ------------

    # profiles = [BezierProfile2D(profile) for profile in transpose_columns(sheets[3])]
    profiles = [Profile2D(profile, name).normalized() for name, profile in transpose_columns(sheets[3])]

    if file_version > 2:
        has_center_cell = not tables[0]["C2"] == 0
        cell_no = (tables[0].num_rows - 2) * 2 + has_center_cell
        geometry = get_geometry_parametric(tables[5], cell_no)
    else:
        geometry = get_geometry_explicit(sheets[0])
        has_center_cell = geometry["shape"].has_center_cell

    balloonings = []
    for i, (name, baloon) in enumerate(transpose_columns(sheets[4])):
        ballooning_type = str(sheets[4][0,2*i+1].value).upper()
        if baloon:
            if ballooning_type == "V1":
                i = 0
                while baloon[i + 1][0] > baloon[i][0]:
                    i += 1

                upper = baloon[:i + 1]
                lower = [(x, -y) for x, y in baloon[i + 1:]]

                ballooning = BallooningBezier(upper, lower, name=name)
                balloonings.append(BallooningBezierNeu.from_classic(ballooning))

            elif ballooning_type == "V2":
                i = 0
                while baloon[i + 1][0] > baloon[i][0]:
                    i += 1

                upper = baloon[:i + 1]
                lower = baloon[i + 1:]

                ballooning = BallooningBezier(upper, lower, name=name)
                balloonings.append(BallooningBezierNeu.from_classic(ballooning))

            elif ballooning_type == "V3":
                balloonings.append(BallooningBezierNeu(baloon))

            else:
                raise ValueError("No ballooning type specified")


    data_dct = {}
    datasheet = tables[-1]
    for row in range(datasheet.num_rows):
        name = datasheet[row, 0]
        if name:
            data_dct[name] = datasheet[row, 1]

    # set stabi cell
    if data_dct.pop("STABICELL", None):
        shape = geometry["shape"]
        if not hasattr(shape, "stabi_cell"):
            raise Exception(f"Cannot add stabi cell on {geometry['shape']}")
        
        shape.stabi_cell = True
        
    attachment_points_cell_table = filter_elements_from_table(cell_sheet, "ATP", 4)
    attachment_points_cell_table.append_right(filter_elements_from_table(cell_sheet, "AHP", 4))

    attachment_points_rib_table = filter_elements_from_table(rib_sheet, "AHP", 3)
    attachment_points_rib_table.append_right(filter_elements_from_table(rib_sheet, "ATP", 3))

    attachment_points = LineSet2D.read_attachment_point_table(
        cell_table=attachment_points_cell_table,
        rib_table=attachment_points_rib_table,
        cell_no=geometry["shape"].cell_num
    )

    attachment_points = {n.name: n for n in attachment_points}

    attachment_points_lower = get_lower_aufhaengepunkte(data_dct)

    def get_grouped_elements(sheet, names, keywords):
        group_kw = keywords[0]
        elements = []
        for name in names:
            elements += read_elements(sheet, name, len_data=len(keywords)-1)
        
        element_dct = to_dct(elements, keywords)

        return group(element_dct, group_kw)


    # RIB HOLES
    rib_holes = HolesTable(rib_sheet)

    rigidfoil_keywords = ["ribs", "start", "end", "distance"]
    rigidfoils = read_elements(rib_sheet, "RIGIDFOIL", len_data=3)
    rigidfoils = to_dct(rigidfoils, rigidfoil_keywords)
    rigidfoils = group(rigidfoils, "ribs")

    cell_rigidfoils = get_grouped_elements(
        cell_sheet, 
        ["RIGIDFOIL"], 
        ["cells", "x_start", "x_end", "y"]
        )


    # CUTS
    def get_cuts(names, target_name):
        objs = []
        for name_src in names:
            objs += read_elements(cell_sheet, name_src, len_data=2)

        cuts_this = [{"cells": cut[0], "left": float(cut[1]), "right": float(cut[2]), "type": target_name} for cut in
                     objs]

        return group(cuts_this, "cells")

    cuts = get_cuts(["EKV", "EKH", "folded"], "folded")
    cuts += get_cuts(["DESIGNM", "DESIGNO", "orthogonal"], "orthogonal")
    cuts += get_cuts(["CUT3D", "cut_3d"], "cut_3d")
    cuts += get_cuts(["singleskin"], "singleskin")

    # Diagonals: center_left, center_right, width_l, width_r, height_l, height_r
    diagonals = DiagonalTable(cell_sheet, file_version)
    straps = StrapTable(cell_sheet)


    material_cells = get_material_codes(cell_sheet)
    material_ribs = get_material_codes(rib_sheet)

    # minirib -> y, start (x)
    miniribs = []
    for minirib in read_elements(cell_sheet, "MINIRIB", len_data=2):
        miniribs.append({
            "yvalue": minirib[1],
            "front_cut": minirib[2],
            "cells": minirib[0]
        })
    miniribs = group(miniribs, "cells")

    lineset_table = tables[6]
    lineset = LineSet2D.read_input_table(lineset_table, attachment_points_lower, attachment_points)
    lineset.set_default_nodes2d_pos(geometry["shape"])

    ballooning_factors = BallooningTable(cell_sheet)
    skin_ribs = SingleSkinTable(rib_sheet)

    glider_2d = Glider2D(elements={"cuts": cuts,
                                   "ballooning_factors": ballooning_factors,
                                   "holes": rib_holes,
                                   "diagonals": diagonals,
                                   "rigidfoils": rigidfoils,
                                   "cell_rigidfoils": cell_rigidfoils,
                                   "straps": straps,
                                   "material_cells": material_cells,
                                   "material_ribs": material_ribs,
                                   "miniribs": miniribs,
                                   "singleskin_ribs": skin_ribs
                                   },
                         profiles=profiles,
                         balloonings=balloonings,
                         lineset=lineset,
                         speed=data_dct.pop("SPEED"),
                         glide=data_dct.pop("GLIDE"),
                         **geometry)
    
    if len(data_dct) > 0:
        logger.error(f"Unknown data keys: {list(data_dct.keys())}")


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
        y += np.cos(alpha) * (span - span_last)
        z -= np.sin(alpha) * (span - span_last)

        alpha += line[4] * np.pi / 180  # angle after the rib

        aoa.append([span, line[5] * np.pi / 180])
        arc.append([y, z])
        front.append([span, -x])
        back.append([span, -x - chord])
        cell_distribution.append([span, i - 1])

        profile_merge.append([span, line[8]])
        ballooning_merge.append([span, line[9]])

        zrot.append([span, line[7] * np.pi / 180])

        span_last = span

    def symmetric_fit(data, bspline=True):
        #not_from_center = int(data[0][0] == 0)
        #mirrored = [[-p[0], p[1]] for p in data[not_from_center:]][::-1] + data
        if bspline:
            return euklid.spline.SymmetricBSplineCurve.fit(data, 3)
        else:
            return euklid.spline.SymmetricBezierCurve.fit(data, 3)

    has_center_cell = not front[0][0] == 0
    cell_no = (len(front) - 1) * 2 + has_center_cell

    start = (2 - has_center_cell) / cell_no

    const_arr = [0.] + np.linspace(start, 1, len(front) - (not has_center_cell)).tolist()
    rib_pos = [0.] + [p[0] for p in front[not has_center_cell:]]
    rib_pos_int = euklid.vector.Interpolation(list(zip(rib_pos, const_arr)))
    rib_distribution = [[i, rib_pos_int.get_value(i)] for i in np.linspace(0, rib_pos[-1], 30)]

    rib_distribution = euklid.spline.BezierCurve.fit(rib_distribution, 3)

    parametric_shape = ParametricShape(symmetric_fit(front), symmetric_fit(back), rib_distribution, cell_no)
    arc_curve = ArcCurve(symmetric_fit(arc))

    return {
        "shape": parametric_shape,
        "arc": arc_curve,
        "aoa": symmetric_fit(aoa),
        "zrot": symmetric_fit(zrot),
        "profile_merge_curve": symmetric_fit(profile_merge, bspline=True),
        "ballooning_merge_curve": symmetric_fit(ballooning_merge, bspline=True)
    }


def get_geometry_parametric(table: Table, cell_num):
    data = {}
    curve_types = {
        "front": euklid.spline.SymmetricBSplineCurve,
        "back": euklid.spline.SymmetricBSplineCurve,
        "rib_distribution": euklid.spline.BezierCurve,
        "arc": euklid.spline.SymmetricBSplineCurve,
        "aoa": euklid.spline.SymmetricBSplineCurve,
        "zrot": euklid.spline.SymmetricBSplineCurve,
        "profile_merge_curve": euklid.spline.SymmetricBSplineCurve,
        "ballooning_merge_curve": euklid.spline.SymmetricBSplineCurve
    }

    for column in range(0, table.num_columns, 2):
        key = table[0, column]
        points = []
        
        if table[0, column+1] is not None:
            curve_type = getattr(euklid.spline, table[0, column+1])
        else:
            logger.warning(f"default curve for {key}")
            curve_type = curve_types[key]

        for row in range(1, table.num_rows):
            if table[row, column] is not None:
                points.append([table[row, column], table[row, column+1]])
        
        data[key] = curve_type(points)
        

    parametric_shape = ParametricShape(
        data["front"], data["back"], data["rib_distribution"], cell_num
    )

    arc_curve = ArcCurve(data["arc"])

    return {
        "shape": parametric_shape,
        "arc": arc_curve,
        "aoa": data["aoa"],
        "zrot": data["zrot"],
        "profile_merge_curve": data["profile_merge_curve"],
        "ballooning_merge_curve": data["ballooning_merge_curve"]
    }
    

def get_material_codes(sheet):
    materials = [[m[0], cloth.get(m[1])] for m in read_elements(sheet, "MATERIAL", len_data=1)]
    i = 0
    ret = []
    while materials:
        codes = [el[1] for el in materials if el[0] == i]
        materials = [el for el in materials if el[0] != i]
        ret.append(codes)
        i += 1
    # cell_no, part_no, code
    return ret


def get_lower_aufhaengepunkte(data):
    aufhaengepunkte = {}

    axis_to_index = {"X": 0, "Y": 1, "Z": 2}
    regex = re.compile("AHP([XYZ])(.*)")

    keys_to_remove = []

    for key in data:
        if isinstance(key, str):
            match = regex.match(key)
            if match:
                axis, name = match.groups()

                aufhaengepunkte.setdefault(name, [0, 0, 0])
                aufhaengepunkte[name][axis_to_index[axis]] = data[key]
                keys_to_remove.append(key)
    
    for key in keys_to_remove:
        data.pop(key)

    return {name: LowerNode2D([0, 0], euklid.vector.Vector3D(position), name)
            for name, position in aufhaengepunkte.items()}


def transpose_columns(sheet, columnswidth=2):
    num_columns = sheet.ncols()
    num_elems = num_columns // columnswidth
    # if num % columnswidth > 0:
    #    raise ValueError("irregular columnswidth")
    result = []
    for col in range(num_elems):
        first_column = col * columnswidth
        last_column = (col + 1) * columnswidth
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


def read_elements(sheet: Table, keyword, len_data=2):
    """
    Return rib/cell_no for the element + data

    -> read_elements(sheet, "AHP", 2) -> [ [rib_no, id, x], ...]
    """

    elements = []
    column = 0
    while column < sheet.num_columns:
        if sheet[0, column] == keyword:
            for row in range(1, sheet.num_rows):
                line = [sheet[row, column + k] for k in range(len_data)]
                
                if line[0] is not None:
                    line.insert(0, row-1)
                    elements.append(line)
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
