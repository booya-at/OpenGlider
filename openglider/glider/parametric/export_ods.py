import copy
from datetime import datetime
import math
from typing import TYPE_CHECKING, List

import euklid
import ezodf
import openglider.glider
import openglider.glider.parametric.glider
from openglider.glider.ballooning import BallooningBezierNeu
from openglider.utils.table import Table

if TYPE_CHECKING:
    from openglider.glider.parametric import ParametricGlider
    from openglider.glider.project import GliderProject

file_version = "V3"

def export_ods_project(glider: "GliderProject", filename):
    
    doc = ezodf.newdoc(doctype="ods")

    for table in get_project_tables(glider):
        doc.sheets.append(table.get_ods_sheet())

    doc.saveas(filename)


def get_split_tables(project: "GliderProject") -> List[Table]:
    tables = []
    tables.append(get_changelog_table(project))
    tables.append(get_parametric_sheet(project.glider))
    tables.append(get_airfoil_sheet(project.glider))
    tables.append(get_ballooning_sheet(project.glider))
    tables.append(get_lines_sheet(project.glider))
    
    tables += project.glider.tables.get_all_tables()

    tables.append(get_data_sheet(project.glider))

    return tables


def get_project_tables(project: "GliderProject") -> List[Table]:
    tables = get_glider_tables(project.glider)
    changelog_table = get_changelog_table(project)

    tables.append(changelog_table)

    return tables

def get_changelog_table(project: "GliderProject") -> Table:
    changelog_table = Table(name="Changelog")
    changelog_table["A1"] = "Date/Time"
    changelog_table["B1"] = "Modification"
    changelog_table["C1"] = "Description"

    for i, change in enumerate(project.changelog):
        dt, name, description = change
        
        changelog_table[i+1, 0] = dt.isoformat()
        changelog_table[i+1, 1] = name
        changelog_table[i+1, 2] = description
    
    return changelog_table



def get_glider_tables(glider: "ParametricGlider") -> List[Table]:
    tables = []

    tables.append(get_geom_sheet(glider))

    attachment_points_rib, attachment_points_cell = glider.lineset.get_attachment_point_table()

    cell_sheet = glider.tables.get_cell_sheet()
    if glider.tables.attachment_points_cell.table.num_columns < 1:
        cell_sheet.append_right(attachment_points_cell)
    rib_sheet = glider.tables.get_rib_sheet()
    if glider.tables.attachment_points_rib.table.num_columns < 1:
        rib_sheet.append_right(attachment_points_rib)

    cell_sheet["A1"] = file_version
    rib_sheet["A1"] = file_version

    tables.append(cell_sheet)
    tables.append(rib_sheet)
    tables.append(get_airfoil_sheet(glider))
    tables.append(get_ballooning_sheet(glider))
    tables.append(get_parametric_sheet(glider))
    tables.append(get_lines_sheet(glider))
    tables.append(get_data_sheet(glider))

    tables.append(glider.curves.table)

    return tables


def export_ods_2d(glider: "ParametricGlider", filename):
    # airfoil sheet
    doc = get_glider_tables(glider)
    doc.saveas(filename)


def get_airfoil_sheet(glider_2d) -> Table:
    profiles = glider_2d.profiles
    table = Table(name="Airfoils")

    for i, profile in enumerate(profiles):
        table[0, 2*i] = profile.name or "unnamed"
        for j, p in enumerate(profile.curve):
            table[j+1, 2*i] = p[0]
            table[j+1, 2*i+1] = p[1]

    return table


def get_geom_sheet(glider_2d) -> Table:
    table = Table(name="geometry")
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

    return table


def get_ballooning_sheet(glider_2d) -> Table:
    balloonings = glider_2d.balloonings
    table = Table(name="Balloonings")
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

    return table

def get_parametric_sheet(glider : "ParametricGlider") -> Table:
    table = Table(name="Parametric")

    def add_curve(name, curve, column_no):
        #sheet.append_columns(2)
        table[0, column_no] = name
        table[0, column_no+1] = type(curve).__name__
        for i, p in enumerate(curve.controlpoints):
            table[i+1, column_no] = p[0]
            table[i+1, column_no+1] = p[1]

    add_curve("front", glider.shape.front_curve, 0)
    add_curve("back", glider.shape.back_curve, 2)
    add_curve("rib_distribution", glider.shape.rib_distribution, 4)
    add_curve("arc", glider.arc.curve, 6)
    add_curve("aoa", glider.aoa, 8)
    add_curve("zrot", glider.zrot, 10)
    add_curve("ballooning_merge_curve", glider.ballooning_merge_curve, 12)
    add_curve("profile_merge_curve", glider.profile_merge_curve, 14)

    return table


def get_lines_sheet(glider, places=3) -> Table:
    table = glider.lineset.get_input_table()
    table.name = "Lines"
    
    return table

def get_data_sheet(glider) -> Table:
    table = Table(name="Data")
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

    return table

# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
