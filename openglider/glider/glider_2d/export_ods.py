import copy

from openglider.glider.cell import DiagonalRib

try:
    import ezodf2 as ezodf
except ImportError:
    import ezodf

import openglider.glider


def export_ods_2d(glider, filename):
    doc = ezodf.newdoc(doctype="ods", filename=filename)
    assert isinstance(glider, openglider.glider.Glider2D)

    doc.sheets.append(get_geom_sheet(glider))
    doc.sheets.append(get_cell_sheet(glider))


    doc.saveas(filename)


def get_geom_sheet(glider_2d):
    geom_page = ezodf.Sheet(name="geometry", size=(glider_2d.half_cell_num + 2, 10))

    # rib_nos
    geom_page[0, 0].set_value("Ribs")
    for i in range(1, glider_2d.half_cell_num+2):
        geom_page[i, 0].set_value(i)

    shape = glider_2d.half_shape()

    geom_page[0, 1].set_value("Chord")
    for i, chord in enumerate(shape.chords):
        geom_page[i+1, 1].set_value(chord)

    geom_page[0, 2].set_value("Le x (m)")
    geom_page[0, 3].set_value("Le y (m)")
    for i, p in enumerate(shape.front):
        geom_page[i+1, 2].set_value(p[0])
        geom_page[i+1, 3].set_value(p[1])

    return geom_page


def get_cell_sheet(glider):
    row_num = glider.half_cell_num
    sheet_name = "Cell Elements"
    sheet = ezodf.Sheet(name=sheet_name, size=(row_num+1, 1))
    elems = glider.elements

    for i in range(1, row_num+1):
        sheet[i, 0].set_value(str(i))

    column = 1

    # cuts
    for cut in elems["cuts"]:
        sheet.append_columns(2)
        # folded -> EKV
        # orthogonal -> DESIGNM
        if cut["type"] == "folded":
            cut_type = "EKV"
        elif cut["type"] == "orthogonal":
            cut_type = "DESIGNM"
        else:
            cut_type = "CUT"
        sheet[0, column].set_value(cut_type)
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

    return sheet


def write_cuts(cuts, sheet):
    pass
    #


# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
