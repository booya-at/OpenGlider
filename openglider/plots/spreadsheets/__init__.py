import ezodf

from openglider.plots.spreadsheets.lines import output_lines
from openglider.plots.spreadsheets.rigidfoils import get_length_table as get_rigidfoils
from openglider.plots.spreadsheets.straps import get_length_table as get_straps
from openglider.plots.spreadsheets.material_list import get_material_sheets


def get_specs(glider):
    sheet = ezodf.Sheet("Tech Specs", size=(100, 10))

    def set_spec(name, value, line):
        sheet[line, 0].set_value(name)
        sheet[line, 1].set_value(value)

    #set_spec("Name", glider.name, 0)
    set_spec("Cells", len(glider.cells), 1)
    set_spec("Area", glider.area, 2)
    set_spec("Area Projected", glider.projected_area, 3)
    set_spec("Aspect Ratio", glider.aspect_ratio, 4)
    set_spec("Span", glider.span, 5)

    return sheet


def get_glider_data(glider):
    specsheet = get_specs(glider)
    linesheet = output_lines(glider)
    rigidfoils = get_rigidfoils(glider)
    straps = get_straps(glider)
    material_sheets = get_material_sheets(glider)

    out_ods = ezodf.newdoc(doctype="ods")
    out_ods.sheets.append(specsheet)
    out_ods.sheets.append(linesheet)
    out_ods.sheets.append(rigidfoils)
    out_ods.sheets.append(straps)

    for sheet in material_sheets:
        out_ods.sheets.append(sheet)

    return out_ods