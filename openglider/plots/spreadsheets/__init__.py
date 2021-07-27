from typing import Dict
import ezodf

from openglider.utils.table import Table
from openglider.lines.line_types.linetype import LineType
from openglider.glider import GliderProject
from openglider.plots.spreadsheets.rigidfoils import get_length_table as get_rigidfoils
from openglider.plots.spreadsheets.straps import get_length_table as get_straps
from openglider.plots.spreadsheets.material_list import get_material_sheets
from openglider.plots.usage_stats import MaterialUsage


def get_glider_data(project: GliderProject, consumption: Dict[str, MaterialUsage]=None) -> ezodf.document.PackagedDocument:
    specsheet = project.get_data_table()
    glider = project.glider_3d
    #specsheet = get_specs(glider)
    glider.lineset.recalc(iterations=30)
    linesheet = glider.lineset.get_table()
    linesheet2 = Table()

    lines = glider.lineset.sort_lines(names=True)
    for i, line in enumerate(lines):
        linesheet2[i+2, 0] = line.name
        linesheet2[i+2, 1] = f"{glider.lineset.get_line_length(line) * 1000:.0f}"
    #linesheet2 = glider.lineset.get_table_2()

    # linesheet = glider.lineset.get_table_2()
    rigidfoils = get_rigidfoils(glider)
    straps = get_straps(glider)
    material_sheets = get_material_sheets(glider)

    consumption_table = Table()
    if consumption:
        for name, usage in consumption.items():
            header = Table()
            header[0, 0] = name
            consumption_table.append_bottom(header, space=1)
            consumption_table.append_bottom(usage.get_table())
    
    line_consumption_table = Table()
    line_consumption = project.glider_3d.lineset.get_consumption()

    linetype: LineType
    row = 0
    for linetype in line_consumption:
        line_consumption_table[row, 0] = linetype.name
        line_consumption_table[row, 1] = round(line_consumption[linetype], 1)
        line_consumption_table[row, 2] = round(linetype.weight * line_consumption[linetype])
        
        row += 1
    
    consumption_table.append_bottom(line_consumption_table, space=1)

    out_ods = ezodf.newdoc(doctype="ods")
    out_ods.sheets.append(specsheet.get_ods_sheet(name="data"))
    out_ods.sheets.append(linesheet.get_ods_sheet(name="lines"))
    out_ods.sheets.append(linesheet2.get_ods_sheet(name="lines_table"))
    out_ods.sheets.append(rigidfoils.get_ods_sheet(name="rigidfoils"))
    out_ods.sheets.append(straps)
    out_ods.sheets.append(consumption_table.get_ods_sheet(name="material consumption"))

    for sheet in material_sheets:
        out_ods.sheets.append(sheet)

    return out_ods