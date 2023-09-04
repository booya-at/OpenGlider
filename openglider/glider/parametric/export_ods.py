from __future__ import annotations

import math
from typing import TYPE_CHECKING

import euklid
import ezodf

from openglider.glider.ballooning import BallooningBezierNeu
from openglider.glider.ballooning.old import BallooningBezier
from openglider.utils.table import Table
from openglider.utils.types import CurveType

if TYPE_CHECKING:
    from openglider.glider.parametric import ParametricGlider
    from openglider.glider.project import GliderProject

file_version = "V4"

def export_ods_project(glider: GliderProject, filename: str) -> None:
    
    doc = ezodf.newdoc(doctype="ods")

    for table in get_project_tables(glider):
        doc.sheets.append(table.get_ods_sheet())

    doc.saveas(filename)


def get_split_tables(project: GliderProject) -> list[Table]:
    tables = []
    tables.append(get_changelog_table(project))
    tables.append(get_parametric_sheet(project.glider))
    tables.append(get_airfoil_sheet(project.glider))
    tables.append(get_ballooning_sheet(project.glider))
    tables.append(get_lines_sheet(project.glider))
    
    tables += project.glider.tables.get_all_tables()

    tables.append(project.glider.config.get_table())

    return tables


def get_project_tables(project: GliderProject) -> list[Table]:
    tables = get_glider_tables(project.glider)
    changelog_table = get_changelog_table(project)

    tables.append(changelog_table)

    return tables

def get_changelog_table(project: GliderProject) -> Table:
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



def get_glider_tables(glider: ParametricGlider) -> list[Table]:
    tables = []

    tables.append(get_geom_sheet(glider))

    cell_sheet = glider.tables.get_cell_sheet()
    rib_sheet = glider.tables.get_rib_sheet()

    tables.append(cell_sheet)
    tables.append(rib_sheet)
    tables.append(get_airfoil_sheet(glider))
    tables.append(get_ballooning_sheet(glider))
    tables.append(get_parametric_sheet(glider))
    tables.append(get_lines_sheet(glider))
    tables.append(glider.config.get_table())

    tables.append(glider.tables.curves.table)

    return tables


def export_ods_2d(glider: ParametricGlider, filename: str) -> None:
    # airfoil sheet
    tables = get_glider_tables(glider)
    Table.save_tables(tables, filename)


def get_airfoil_sheet(glider_2d: ParametricGlider) -> Table:
    profiles = glider_2d.profiles
    table = Table(name="Airfoils")

    for i, profile in enumerate(profiles):
        table[0, 2*i] = profile.name or "unnamed"
        for j, p in enumerate(profile.curve):
            table[j+1, 2*i] = p[0]
            table[j+1, 2*i+1] = p[1]

    return table


def get_geom_sheet(glider_2d: ParametricGlider) -> Table:
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

    for i, x in enumerate(glider_2d.shape.rib_x_values[center_cell:]):
        table[i+1, 3] = x
    # set arc values
    table[0, 4] = "Arc"
    last_angle = 0.
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

    def interpolation(curve: CurveType) -> euklid.vector.Interpolation:
        return euklid.vector.Interpolation(curve.get_sequence(100).nodes)

    aoa_int = interpolation(glider_2d.aoa)
    profile_int = interpolation(glider_2d.profile_merge_curve)
    ballooning_int = interpolation(glider_2d.ballooning_merge_curve)

    for rib_no, x in enumerate(glider_2d.shape.rib_x_values[center_cell:]):
        table[rib_no+1, 0] = rib_no+1
        table[rib_no+1, 5] = aoa_int.get_value(x)*180/math.pi
        table[rib_no+1, 6] = 0
        table[rib_no+1, 7] = 0
        table[rib_no+1, 8] = profile_int.get_value(x)
        table[rib_no+1, 9] = ballooning_int.get_value(x)
    
    if glider_2d.shape.stabi_cell:
        table = table.get_rows(0, table.num_rows-1)

    return table


def get_ballooning_sheet(glider_2d: ParametricGlider) -> Table:
    balloonings = glider_2d.balloonings
    table = Table(name="Balloonings")
    #row_num = max([len(b.upper_spline.controlpoints)+len(b.lower_spline.controlpoints) for b in balloonings])+1
    #sheet = ezodf.Sheet(name="Balloonings", size=(row_num, 2*len(balloonings)))

    for ballooning_no, ballooning in enumerate(balloonings):
        
        #sheet.append_columns(2)
        table[0, 2*ballooning_no] = f"ballooning_{ballooning_no}"
        if isinstance(ballooning, BallooningBezierNeu):
            table[0, 2*ballooning_no+1] = "V3"
            pts = list(ballooning.controlpoints)
        elif isinstance(ballooning, BallooningBezier):
            table[0, 2*ballooning_no+1] = "V2"
            pts = list(ballooning.upper_spline.controlpoints) + list(ballooning.lower_spline.controlpoints)
        else:
            raise ValueError("Wrong ballooning type")

        for i, point in enumerate(pts):
            table[i+1, 2*ballooning_no] = point[0]
            table[i+1, 2*ballooning_no+1] = point[1]

    return table

def get_parametric_sheet(glider : ParametricGlider) -> Table:
    table = Table(name="Parametric")

    def add_curve(name: str, curve: CurveType, column_no: int) -> None:
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


def get_lines_sheet(glider: ParametricGlider, places: int=3) -> Table:
    table = glider.tables.lines.table
    table.name = "Lines"
    
    return table

# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
