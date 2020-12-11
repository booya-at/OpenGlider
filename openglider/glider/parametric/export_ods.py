import copy
import math

import ezodf

import openglider.glider
import openglider.glider.parametric.glider
from openglider.glider.ballooning import BallooningBezierNeu
from openglider.glider.cell import DiagonalRib
from openglider.glider.parametric.arc import ArcCurve
from openglider.utils.table import Table

file_version = "V3"

def export_ods_2d(glider, filename):
    doc = ezodf.newdoc(doctype="ods", filename=filename)
    assert isinstance(glider, openglider.glider.parametric.glider.ParametricGlider)

    doc.sheets.append(get_geom_sheet(glider))

    # rename attachment points in case!
    lines_sheet = get_lines_sheet(glider)
    
    cell_sheet = get_cell_sheet(glider)
    cell_sheet.name = "Cell Elements"
    rib_sheet = get_rib_sheet(glider)
    rib_sheet.name = "Rib Elements"
    
    attachment_points = glider.lineset.get_attachment_point_table()
    rib_sheet.append_right(attachment_points[0])
    cell_sheet.append_right(attachment_points[1])

    doc.sheets.append(cell_sheet.get_ods_sheet())
    doc.sheets.append(rib_sheet.get_ods_sheet())
    doc.sheets.append(get_airfoil_sheet(glider))
    doc.sheets.append(get_ballooning_sheet(glider))
    doc.sheets.append(get_parametric_sheet(glider))
    doc.sheets.append(lines_sheet)
    doc.sheets.append(get_data_sheet(glider))

    # airfoil sheet



    doc.saveas(filename)


def get_airfoil_sheet(glider_2d):
    profiles = glider_2d.profiles
    max_length = max(len(p) for p in profiles)
    sheet = ezodf.Sheet(name="Airfoils", size=(max_length+1, len(profiles)*2))

    for i, profile in enumerate(profiles):
        sheet[0, 2*i].set_value(profile.name or "unnamed")
        for j, p in enumerate(profile):
            sheet[j+1, 2*i].set_value(p[0])
            sheet[j+1, 2*i+1].set_value(p[1])

    return sheet


def get_geom_sheet(glider_2d):
    geom_page = ezodf.Sheet(name="geometry", size=(glider_2d.shape.half_cell_num + 2, 10))

    # rib_nos
    geom_page[0, 0].set_value("Ribs")

    shape = glider_2d.shape.get_half_shape()

    geom_page[0, 1].set_value("Chord")
    for i, chord in enumerate(shape.chords):
        geom_page[i+1, 1].set_value(chord)

    geom_page[0, 2].set_value("Le x (m)")
    geom_page[0, 3].set_value("Le y (m)")
    for i, p in enumerate(shape.front):
        geom_page[i+1, 2].set_value(p[0])
        geom_page[i+1, 3].set_value(-p[1])

    # set arc values
    geom_page[0, 4].set_value("Arc")
    last_angle = 0
    cell_angles = glider_2d.arc.get_cell_angles(glider_2d.shape.rib_x_values)
    if glider_2d.shape.has_center_cell:
        cell_angles = cell_angles[1:]
    for i, angle in enumerate(cell_angles + [cell_angles[-1]]):
        this_angle = angle * 180/math.pi

        geom_page[i+1, 4].set_value(this_angle-last_angle)
        last_angle = this_angle

    geom_page[0, 5].set_value("AOA")
    geom_page[0, 6].set_value("Z-rotation")
    geom_page[0, 7].set_value("Y-rotation")
    geom_page[0, 8].set_value("profile-merge")
    geom_page[0, 9].set_value("ballooning-merge")
    aoa_int = glider_2d.aoa.interpolation(num=100)
    profile_int = glider_2d.profile_merge_curve.interpolation(num=100)
    ballooning_int = glider_2d.ballooning_merge_curve.interpolation(num=100)
    for rib_no, x in enumerate(glider_2d.shape.rib_x_values):
        geom_page[rib_no+1, 0].set_value(rib_no+1)
        geom_page[rib_no+1, 5].set_value(aoa_int(x)*180/math.pi)
        geom_page[rib_no+1, 6].set_value(0)
        geom_page[rib_no+1, 7].set_value(0)
        geom_page[rib_no+1, 8].set_value(profile_int(x))
        geom_page[rib_no+1, 9].set_value(ballooning_int(x))

    return geom_page


def get_cell_sheet(glider):
    cell_num = glider.shape.half_cell_num
    row_num = glider.shape.half_cell_num
    table = Table()
    table["A1"] = file_version

    for i in range(1, row_num+1):
        table[i, 0] = str(i)

    elems = glider.elements

    # cuts
    cuts_table = Table()
    cuts_per_cell = []
    for cell_no in range(cell_num):
        cuts_this = []
        for cut in elems.get("cuts", []):
            if cell_no in cut["cells"]:
                cuts_this.append((cut["left"], cut["right"], cut["type"]))

        cuts_this.sort(key=lambda x: sum(x[:2]))
        cuts_per_cell.append(cuts_this)

    def find_next(cut, cell_no):
        cuts_this = cuts_per_cell[cell_no]
        for new_cut in cuts_this:
            if cut[1] == new_cut[0] and new_cut[2] == cut[2]:
                cuts_this.remove(new_cut)
                return new_cut

    def add_column(cell_no):
        cuts_this = cuts_per_cell[cell_no]
        if not cuts_this:
            return False

        cut = cuts_this[0]
        column = Table()
        column[0, 0] = cut[2]
        column.insert_row(cut[:2], cell_no+1)
        cuts_this.remove(cut)


        for cell_no_temp in range(cell_no+1, cell_num):
            cut_next = find_next(cut, cell_no_temp)
            if not cut_next:
                break
            column.insert_row(cut_next[:2], cell_no_temp+1)
            cut = cut_next

        cuts_table.append_right(column)

        return column

    for cell_no in range(cell_num):
        while add_column(cell_no):
            pass

    table.append_right(cuts_table)

    # Diagonals
    for diagonal in elems.get("diagonals", []):
        diagonal_table = Table()
        diagonal = copy.copy(diagonal)
        diagonal_table[0, 0] = "QR"
        cells = diagonal.pop("cells")
        _diagonal = DiagonalRib(**diagonal)

        for cell_no in cells:
            # center_left, center_right, width_left, width_right, height_left, height_right

            diagonal_table[cell_no+1, 0] = _diagonal.center_left
            diagonal_table[cell_no+1, 1] = _diagonal.center_right
            diagonal_table[cell_no+1, 2] = _diagonal.width_left
            diagonal_table[cell_no+1, 3] = _diagonal.width_right
            diagonal_table[cell_no+1, 4] = _diagonal.left_front[1]
            diagonal_table[cell_no+1, 5] = _diagonal.right_front[1]

        table.append_right(diagonal_table)

    # Straps
    for strap in elems.get("straps", []):
        strap_table = Table()
        strap_table[0, 0] = "STRAP"
        for cell_no in strap["cells"]:
            # 
            strap_table[cell_no+1, 0] = strap["left"]
            strap_table[cell_no+1, 1] = strap["right"]
            strap_table[cell_no+1, 2] = strap["width"]

        table.append_right(strap_table)

    # Material
    material_table = Table()
    for cell_no, cell in enumerate(elems.get("materials", [])):
        for part_no, part in enumerate(cell):
            material_table[cell_no+1, part_no] = part

    for part_no in range(material_table.num_columns):
        material_table[0, part_no] = "MATERIAL"

    table.append_right(material_table)

    return table


def get_rib_sheet(glider_2d):
    table = Table()
    table[0, 0] = file_version

    for i in range(1, glider_2d.shape.half_cell_num+1):
        table[i, 0] = f"rib{i}"

    # holes
    for hole in glider_2d.elements.get("holes", []):
        hole_table = Table()

        hole_table[0, 0] = "HOLE"

        for rib_no in hole["ribs"]:
            hole_table[rib_no+1, 0] = hole["pos"]
            hole_table[rib_no+1, 1] = hole["size"]
        
        table.append_right(hole_table)

    # rigidfoils
    rigidfoils = glider_2d.elements.get("rigidfoils", [])
    rigidfoils.sort(key=lambda r: r["start"])
    for rigidfoil in rigidfoils:
        rigidfoil_table = Table()
        rigidfoil_table[0, 0] = "RIGIDFOIL"

        for rib_no in rigidfoil["ribs"]:
            rigidfoil_table[rib_no+1, 0] = rigidfoil["start"]
            rigidfoil_table[rib_no+1, 1] = rigidfoil["end"]
            rigidfoil_table[rib_no+1, 2] = rigidfoil["distance"]
        
        table.append_right(rigidfoil_table)

    return table


def get_ballooning_sheet(glider_2d):
    balloonings = glider_2d.balloonings
    table = Table()
    #row_num = max([len(b.upper_spline.controlpoints)+len(b.lower_spline.controlpoints) for b in balloonings])+1
    #sheet = ezodf.Sheet(name="Balloonings", size=(row_num, 2*len(balloonings)))

    for ballooning_no, ballooning in enumerate(balloonings):
        #sheet.append_columns(2)
        table[0, 2*ballooning_no] = "ballooning_{}".format(ballooning_no)
        if type(ballooning) is BallooningBezierNeu:
            table[0, 2*ballooning_no+1] = "V3"
            pts = ballooning.controlpoints
        else:
            table[0, 2*ballooning_no+1] = "V2"
            pts = list(ballooning.upper_spline.controlpoints) + list(ballooning.lower_spline.controlpoints)

        for i, point in enumerate(pts):
            table[i+1, 2*ballooning_no] = point[0]
            table[i+1, 2*ballooning_no+1] = point[1]

    ods_sheet = table.get_ods_sheet()
    ods_sheet.name = "Balloonings"
    return ods_sheet


def get_parametric_sheet(glider : "openglider.glider.parametric.glider.ParametricGlider"):
    line_no = 1 + max([
        glider.shape.front_curve.numpoints,
        glider.shape.back_curve.numpoints,
        glider.shape.rib_distribution.numpoints,
        glider.arc.curve.numpoints,
        glider.zrot.numpoints,
        glider.aoa.numpoints,
        glider.ballooning_merge_curve.numpoints,
        glider.profile_merge_curve.numpoints
        ])
    sheet = ezodf.Sheet(name="Parametric", size=(line_no, 16))

    def add_curve(name, curve, column_no):
        #sheet.append_columns(2)
        sheet[0, column_no].set_value(name)
        for i, p in enumerate(curve):
            sheet[i+1, column_no].set_value(p[0])
            sheet[i+1, column_no+1].set_value(p[1])

    add_curve("front", glider.shape.front_curve.controlpoints, 0)
    add_curve("back", glider.shape.back_curve.controlpoints, 2)
    add_curve("rib_distribution", glider.shape.rib_distribution.controlpoints, 4)
    add_curve("arc", glider.arc.curve.controlpoints, 6)
    add_curve("aoa", glider.aoa.controlpoints, 8)
    add_curve("zrot", glider.zrot.controlpoints, 10)
    add_curve("ballooning_merge_curve", glider.ballooning_merge_curve.controlpoints, 12)
    add_curve("profile_merge_curve", glider.profile_merge_curve.controlpoints, 14)

    return sheet


def get_lines_sheet(glider, places=3):
    table = glider.lineset.get_input_table()
    ods_sheet = table.get_ods_sheet("Lines")
    return ods_sheet

def get_data_sheet(glider):
    ods_sheet = ezodf.Sheet(name="Data", size=(3, 10))
    ods_sheet[0,0].set_value("Data")
    current_row = 1
    # lower attachment_points
    for pt_no, att_pt in enumerate(glider.lineset.get_lower_attachment_points()):
        ods_sheet.append_rows(3)
        for i, axis in enumerate(['X', 'Y', 'Z']):
            ods_sheet[current_row + i, 0].set_value("AHP{}{}".format(axis, att_pt.name))
            ods_sheet[current_row + i, 1].set_value(att_pt.pos_3D[i])
        current_row += 3

    ods_sheet[current_row, 0].set_value("SPEED")
    ods_sheet[current_row, 1].set_value(glider.speed)

    ods_sheet[current_row+1, 0].set_value("GLIDE")
    ods_sheet[current_row+1, 1].set_value(glider.glide)



    return ods_sheet

# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
