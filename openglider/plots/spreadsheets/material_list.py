from typing import Tuple, List

from openglider.glider.cell.diagonals import DiagonalRib
from openglider.glider.cell.panel import Panel
from openglider.glider.glider import Glider
from openglider.utils.table import Table


def get_material_sheets(glider: Glider) -> Tuple[Table, Table, Table]:
    # ribs
    ribs_sheet = Table(name="material_ribs")

    ribs_sheet[0, 0] = "Rib"
    ribs_sheet[0, 1] = "Material"
    for rib_no, rib in enumerate(glider.ribs):
        ribs_sheet[rib_no+1, 0] = rib.name
        ribs_sheet[rib_no+1, 1] = str(rib.material)

    # panels
    panel_sheet = Table(name="material_panels")

    panel_sheet[0, 0] = "Cell"
    panel_sheet[0, 1] = "Panel"
    panel_sheet[0, 2] = "Material"
    current_line = 1
    for cell_no, cell in enumerate(glider.cells):
        for panel_no, panel in enumerate(cell.panels):
            panel_sheet[current_line, 0] = cell.name
            panel_sheet[current_line, 1] = panel.name
            panel_sheet[current_line, 2] = str(panel.material)
            current_line += 1

    # dribs
    all_dribs: List[DiagonalRib] = sum([cell.diagonals for cell in glider.cells], [])
    dribs_sheet = Table(name="material_dribs")

    current_line = 1
    dribs_sheet[0, 0] = "Cell"
    dribs_sheet[0, 1] = "Diagonal"
    dribs_sheet[0, 2] = "Material"

    for cell in glider.cells:
        for drib_no, drib in enumerate(cell.diagonals):
            dribs_sheet[current_line, 0] = cell.name
            dribs_sheet[current_line, 1] = drib.name
            dribs_sheet[current_line, 2] = drib.material_code
            current_line += 1

    return ribs_sheet, panel_sheet, dribs_sheet
