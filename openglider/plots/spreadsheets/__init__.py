import ezodf

from openglider.plots.spreadsheets.lines import output_lines
from openglider.plots.spreadsheets.rigidfoils import get_length_table as get_rigidfoils
from openglider.plots.spreadsheets.straps import get_length_table as get_straps
from openglider.plots.spreadsheets.material_list import get_material_sheets


def get_glider_data(glider):
    linesheet = output_lines(glider)
    rigidfoils = get_rigidfoils(glider)
    straps = get_straps(glider)
    material_sheets = get_material_sheets(glider)

    out_ods = ezodf.newdoc(doctype="ods")
    out_ods.sheets.append(linesheet)
    out_ods.sheets.append(rigidfoils)
    out_ods.sheets.append(straps)

    for sheet in material_sheets:
        out_ods.sheets.append(sheet)

    return out_ods