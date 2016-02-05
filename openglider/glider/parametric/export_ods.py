import copy

import math

import openglider.glider.parametric.glider
from openglider.glider.cell import DiagonalRib
from openglider.glider.parametric.arc import ArcCurve

try:
    import ezodf2 as ezodf
except ImportError:
    import ezodf

import openglider.glider


def export_ods_2d(glider, filename):
    doc = ezodf.newdoc(doctype="ods", filename=filename)
    assert isinstance(glider, openglider.glider.parametric.glider.ParametricGlider)

    doc.sheets.append(get_geom_sheet(glider))
    doc.sheets.append(get_cell_sheet(glider))
    doc.sheets.append(get_rib_sheet(glider))
    doc.sheets.append(get_airfoil_sheet(glider))
    doc.sheets.append(get_ballooning_sheet(glider))
    doc.sheets.append(get_parametric_sheet(glider))
    doc.sheets.append(get_lines_sheet(glider))
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
    for i, angle in enumerate(cell_angles):
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
    row_num = glider.shape.half_cell_num
    sheet_name = "Cell Elements"
    sheet = ezodf.Sheet(name=sheet_name, size=(row_num+1, 1))
    elems = glider.elements

    for i in range(1, row_num+1):
        sheet[i, 0].set_value(str(i))

    column = 1

    # cuts
    for cut in elems["cuts"]:
        sheet.append_columns(2)
        # folded = EKV
        # orthogonal = DESIGNM
        sheet[0, column].set_value(cut["type"])
        for cell_no in cut["cells"]:
            sheet[cell_no+1, column].set_value(cut["left"])
            sheet[cell_no+1, column+1].set_value(cut["right"])
        column += 2

    # Diagonals
    for diagonal in elems["diagonals"]:
        diagonal = copy.copy(diagonal)
        sheet.append_columns(6)
        sheet[0, column].set_value("QR")
        cells = diagonal.pop("cells")
        _diagonal = DiagonalRib(**diagonal)

        for cell_no in cells:
            # center_left, center_right, width_left, width_right, height_left, height_right

            sheet[cell_no+1, column].set_value(_diagonal.center_left)
            sheet[cell_no+1, column+1].set_value(_diagonal.center_right)
            sheet[cell_no+1, column+2].set_value(_diagonal.width_left)
            sheet[cell_no+1, column+3].set_value(_diagonal.width_right)
            sheet[cell_no+1, column+4].set_value(_diagonal.left_front[1])
            sheet[cell_no+1, column+5].set_value(_diagonal.right_front[1])
        column += 6

    # Straps
    for strap in elems["straps"]:
        sheet.append_columns(2)
        sheet[0, column].set_value("VEKTLAENGE")
        for cell_no in strap["cells"]:
            sheet[cell_no+1, column].set_value(strap["left"])
            sheet[cell_no+1, column+1].set_value(strap["right"])
        column += 2

    # Material
    max_parts = max([len(c) for c in elems["materials"]])
    sheet.append_columns(max_parts)
    for part_no in range(max_parts):
        sheet[0, column+part_no].set_value("MATERIAL")
    for cell_no, cell in enumerate(elems["materials"]):
        for part_no, part in enumerate(cell):
            sheet[cell_no+1, column+part_no].set_value(part)

    return sheet


def get_rib_sheet(glider_2d):
    row_num = glider_2d.shape.half_cell_num + 1
    sheet_name = "Rib Elements"
    sheet = ezodf.Sheet(name=sheet_name, size=(row_num+1, 1))
    elems = glider_2d.elements

    for i in range(1, row_num+1):
        sheet[i, 0].set_value(str(i))

    column = 1

    # holes
    for hole in elems["holes"]:
        sheet.append_columns(2)

        sheet[0, column].set_value("QUERLOCH")

        for rib_no in hole["ribs"]:
            sheet[rib_no+1, column].set_value(hole["pos"])
            sheet[rib_no+1, column+1].set_value(hole["size"])

        column += 2

    # attachment points
    per_rib = [glider_2d.lineset.get_upper_nodes(rib_no) for rib_no in range(glider_2d.shape.half_rib_num)]
    max_points = max([len(p) for p in per_rib])
    sheet.append_columns(3*max_points)

    for node_no in range(max_points):
        sheet[0, column+3*node_no].set_value("AHP")

    for rib_no, nodes in enumerate(per_rib):
        nodes.sort(key=lambda node: node.rib_pos)
        for node_no, node in enumerate(nodes):
            sheet[rib_no+1, column+3*node_no].set_value(node.name)
            sheet[rib_no+1, column+3*node_no+1].set_value(node.rib_pos)
            sheet[rib_no+1, column+3*node_no+2].set_value(node.force)
    column += 3*max_points

    # rigidfoils
    rigidfoils = glider_2d.elements.get("rigidfoils", [])
    rigidfoils.sort(key=lambda r: r["start"])
    for rigidfoil in rigidfoils:
        sheet.append_columns(3)
        sheet[0, column].set_value("RIGIDFOIL")
        for rib_no in rigidfoil["ribs"]:
            sheet[rib_no+1, column].set_value(rigidfoil["start"])
            sheet[rib_no+1, column+1].set_value(rigidfoil["end"])
            sheet[rib_no+1, column+1].set_value(rigidfoil["distance"])
        column += 3

    return sheet


def get_ballooning_sheet(glider_2d):
    balloonings = glider_2d.balloonings
    line_no = max([len(b.upper_spline.controlpoints)+len(b.lower_spline.controlpoints) for b in balloonings])+1
    sheet = ezodf.Sheet(name="Balloonings", size=(line_no, 2*len(balloonings)))

    for ballooning_no, ballooning in enumerate(balloonings):
        #sheet.append_columns(2)
        sheet[0, 2*ballooning_no].set_value("ballooning_{}".format(ballooning_no))
        pts = list(ballooning.upper_spline.controlpoints) + list(ballooning.lower_spline.controlpoints)
        for i, point in enumerate(pts):
            sheet[i+1, 2*ballooning_no].set_value(point[0])
            sheet[i+1, 2*ballooning_no+1].set_value(point[0])

    return sheet


def get_parametric_sheet(glider):
    line_no = 1 + max([
        glider.shape.front_curve.numpoints,
        glider.shape.back_curve.numpoints,
        glider.shape.rib_distribution.numpoints,
        glider.arc.curve.numpoints
        ])
    sheet = ezodf.Sheet(name="Parametric", size=(line_no, 8))

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

    return sheet


def get_lines_sheet(glider, places=3):
    lower_nodes = glider.lineset.get_lower_attachment_points()

    line_trees = [glider.lineset.create_tree(node) for node in lower_nodes]
    ods_sheet = ezodf.Table(name="Lines", size=(500, 500))

    def insert_block(line, upper, row, column):
        ods_sheet[row, column+1].set_value(line.line_type.name)
        if upper:
            ods_sheet[row, column].set_value(line.target_length)
            for line, line_upper in upper:
                row = insert_block(line, line_upper, row, column+2)
        else:  # Insert a top node
            name = line.upper_node.name
            if not name:
                name = "Rib_{}/{}".format(line.upper_node.rib_no,
                                          line.upper_node.rib_pos)
            ods_sheet[row, column].set_value(name)
            row += 1
        return row

    row = 0
    for node_no, tree in enumerate(line_trees):
        ods_sheet[row, 0].set_value(node_no)
        for line, upper in tree:
            row = insert_block(line, upper, row, 1)

    return ods_sheet

def get_data_sheet(glider):
    ods_sheet = ezodf.Sheet(name="Data", size=(1,10))
    ods_sheet[0,0].set_value("Data")
    current_row = 1
    # lower attachment_points
    for pt_no, att_pt in enumerate(glider.lineset.get_lower_attachment_points()):
        ods_sheet.append_rows(3)
        for i, axis in enumerate(['X', 'Y', 'Z']):
            ods_sheet[current_row + i, 0].set_value("AHP{}{}".format(axis, pt_no))
            ods_sheet[current_row + i, 1].set_value(att_pt.pos_3D[i])
        current_row += 3

    return ods_sheet

# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
