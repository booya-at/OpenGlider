from typing import Tuple, List

from openglider.glider.cell.elements import DiagonalRib
from openglider.glider.cell.panel import Panel
from openglider.utils.table import Table


def get_material_sheets(glider) -> Tuple[Table, Table, Table]:
    # ribs
    ribs_sheet = Table(name="material_ribs")

    ribs_sheet[0, 0] = "Rib"
    ribs_sheet[0, 1] = "Material"
    for rib_no, rib in enumerate(glider.ribs):
        ribs_sheet[rib_no+1, 0] = rib.name
        ribs_sheet[rib_no+1, 1] = str(rib.material)

    # panels
    all_panels: List[Panel] = sum([cell.panels for cell in glider.cells], [])

    panel_sheet = Table(name="material_panels")

    panel_sheet[0, 0] = "Panel"
    panel_sheet[0, 1] = "Material"
    for panel_no, panel in enumerate(all_panels):
        panel_sheet[panel_no+1, 0] = panel.name
        panel_sheet[panel_no+1, 1] = str(panel.material)

    # dribs
    all_dribs: List[DiagonalRib] = sum([cell.diagonals for cell in glider.cells], [])
    dribs_sheet = Table(name="material_dribs")

    dribs_sheet[0, 0] = "Diagonal"
    dribs_sheet[0, 1] = "Material"
    for drib_no, drib in enumerate(all_dribs):
        dribs_sheet[drib_no+1, 0] = drib.name
        dribs_sheet[drib_no+1, 1] = drib.material_code

    return ribs_sheet, panel_sheet, dribs_sheet
