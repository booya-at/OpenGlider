import copy
import math

import euklid
import ezodf
import openglider.glider
import openglider.glider.parametric.glider
from openglider.glider.ballooning import BallooningBezierNeu
from openglider.utils.table import Table

file_version = "V3"

def export_ods_2d(glider, filename):
    doc = ezodf.newdoc(doctype="ods", filename=filename)
    assert isinstance(glider, openglider.glider.parametric.glider.ParametricGlider)

    doc.sheets.append(get_geom_sheet(glider))
    
    cell_sheet = get_cell_sheet(glider)
    cell_sheet.name = "Cell Elements"
    rib_sheet = get_rib_sheet(glider)
    rib_sheet.name = "Rib Elements"
    
    attachment_points = glider.lineset.get_attachment_point_table()

    if "attachment_points_rib" in glider.elements:
        rib_sheet.append_right(glider.elements["attachment_points_rib"].table)
    else:
        rib_sheet.append_right(attachment_points[0])
    
    if "attachment_points_cell" in glider.elements:
        cell_sheet.append_right(glider.elements["attachment_points_cell"].table)
    else:
        cell_sheet.append_right(attachment_points[1])

    doc.sheets.append(cell_sheet.get_ods_sheet())
    doc.sheets.append(rib_sheet.get_ods_sheet())
    doc.sheets.append(get_airfoil_sheet(glider))
    doc.sheets.append(get_ballooning_sheet(glider))
    doc.sheets.append(get_parametric_sheet(glider))
    doc.sheets.append(get_lines_sheet(glider))
    doc.sheets.append(get_data_sheet(glider))

    doc.sheets.append(glider.curves.table.get_ods_sheet("Curves"))

    # airfoil sheet



    doc.saveas(filename)


def get_airfoil_sheet(glider_2d):
    profiles = glider_2d.profiles
    max_length = max(p.numpoints for p in profiles)
    sheet = ezodf.Sheet(name="Airfoils", size=(max_length+1, len(profiles)*2))

    for i, profile in enumerate(profiles):
        sheet[0, 2*i].set_value(profile.name or "unnamed")
        for j, p in enumerate(profile.curve):
            sheet[j+1, 2*i].set_value(p[0])
            sheet[j+1, 2*i+1].set_value(p[1])

    return sheet


def get_geom_sheet(glider_2d):
    table = Table()
    #geom_page = ezodf.Sheet(name="geometry", size=(glider_2d.shape.half_cell_num + 2, 10))

    # rib_nos
    table[0, 0] = "Ribs"

    shape = glider_2d.shape.get_half_shape()    
    center_cell = glider_2d.shape.has_center_cell

    table[0, 1] = "Chord"
    for i, chord in enumerate(shape.chords[center_cell:]):
        table[i+1, 1] = chord

    table[0, 2] = "Le x (m)"
    table[0, 3] = "Le y (m)"
    for i, p in enumerate(shape.front.nodes[center_cell:]):
        table[i+1, 2] = p[0]
        table[i+1, 3] = -p[1]

    for i, p in enumerate(glider_2d.shape.rib_x_values):
        table[i+1, 3] = p
    # set arc values
    table[0, 4] = "Arc"
    last_angle = 0
    cell_angles = glider_2d.arc.get_cell_angles(glider_2d.shape.rib_x_values)
    if glider_2d.shape.has_center_cell:
        cell_angles = cell_angles[1:]
    for i, angle in enumerate(cell_angles + [cell_angles[-1]]):
        this_angle = angle * 180/math.pi

        table[i+1, 4] = this_angle-last_angle
        last_angle = this_angle

    table[0, 5] = "AOA"
    table[0, 6] = "Z-rotation"
    table[0, 7] = "Y-rotation"
    table[0, 8] = "profile-merge"
    table[0, 9] = "ballooning-merge"

    def interpolation(curve):
        return euklid.vector.Interpolation(curve.get_sequence(100).nodes)

    aoa_int = interpolation(glider_2d.aoa)
    profile_int = interpolation(glider_2d.profile_merge_curve)
    ballooning_int = interpolation(glider_2d.ballooning_merge_curve)

    for rib_no, x in enumerate(glider_2d.shape.rib_x_values):
        table[rib_no+1, 0] = rib_no+1
        table[rib_no+1, 5] = aoa_int.get_value(x)*180/math.pi
        table[rib_no+1, 6] = 0
        table[rib_no+1, 7] = 0
        table[rib_no+1, 8] = profile_int.get_value(x)
        table[rib_no+1, 9] = ballooning_int.get_value(x)
    
    if glider_2d.shape.stabi_cell:
        table = table.get_rows(0, table.num_rows-1)

    return table.get_ods_sheet(name="geometry")


def get_cell_sheet(glider):
    row_num = glider.shape.half_cell_num
    table = Table()
    table["A1"] = file_version

    for i in range(1, row_num+1):
        table[i, 0] = str(i)

    elems = glider.elements

    table.append_right(elems["cell_rigidfoils"].table)

    # cuts
    table.append_right(elems["cuts"].table)

    # Diagonals
    table.append_right(elems["diagonals"].table)
    table.append_right(elems["straps"].table)

    table.append_right(elems["material_cells"].table)

    if "ballooning_factors" in elems:
        table.append_right(elems["ballooning_factors"].table)

    return table


def get_rib_sheet(glider_2d):
    table = Table()
    table[0, 0] = file_version
    elems = glider_2d.elements

    for i in range(1, glider_2d.shape.half_cell_num+1):
        table[i, 0] = f"rib{i}"

    table.append_right(glider_2d.elements["holes"].table)    
    table.append_right(glider_2d.elements["rigidfoils"].table)
    table.append_right(glider_2d.elements["material_ribs"].table)

    if "singleskin_ribs" in elems:
        table.append_right(elems["singleskin_ribs"].table)

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
    line_no = 1 + max([len(curve.controlpoints) for curve in [
        glider.shape.front_curve,
        glider.shape.back_curve,
        glider.shape.rib_distribution,
        glider.arc.curve,
        glider.zrot,
        glider.aoa,
        glider.ballooning_merge_curve,
        glider.profile_merge_curve
        ]])
    sheet = ezodf.Sheet(name="Parametric", size=(line_no, 16))

    def add_curve(name, curve, column_no):
        #sheet.append_columns(2)
        sheet[0, column_no].set_value(name)
        sheet[0, column_no+1].set_value(type(curve).__name__)
        for i, p in enumerate(curve.controlpoints):
            sheet[i+1, column_no].set_value(p[0])
            sheet[i+1, column_no+1].set_value(p[1])

    add_curve("front", glider.shape.front_curve, 0)
    add_curve("back", glider.shape.back_curve, 2)
    add_curve("rib_distribution", glider.shape.rib_distribution, 4)
    add_curve("arc", glider.arc.curve, 6)
    add_curve("aoa", glider.aoa, 8)
    add_curve("zrot", glider.zrot, 10)
    add_curve("ballooning_merge_curve", glider.ballooning_merge_curve, 12)
    add_curve("profile_merge_curve", glider.profile_merge_curve, 14)

    return sheet


def get_lines_sheet(glider, places=3):
    table = glider.lineset.get_input_table()
    ods_sheet = table.get_ods_sheet("Lines")
    return ods_sheet

def get_data_sheet(glider):
    table = Table()
    table[0,0] = "Data"

    current_row = 1
    # lower attachment_points
    for att_pt in glider.lineset.get_lower_attachment_points():
        for i, axis in enumerate(['X', 'Y', 'Z']):
            table[current_row + i, 0] = "AHP{}{}".format(axis, att_pt.name)
            table[current_row + i, 1] = att_pt.pos_3D[i]
        current_row += 3

    table[current_row, 0] = "SPEED"
    table[current_row, 1] = glider.speed

    table[current_row+1, 0] = "GLIDE"
    table[current_row+1, 1] = glider.glide

    table[current_row+2, 0] = "STABICELL"
    if glider.shape.stabi_cell:
        table[current_row+2, 1] = "1"

    table[current_row+3, 0] = "version"
    table[current_row+3, 1] = openglider.__version__


    return table.get_ods_sheet(name="Data")

# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
