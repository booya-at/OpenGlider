import ezodf


def get_material_sheets(glider):
    # ribs
    ribs_sheet = ezodf.Table(name="material_ribs", size=(len(glider.ribs)+2, 2))

    ribs_sheet[0, 0].set_value("Rib")
    ribs_sheet[0, 1].set_value("Material")
    for rib_no, rib in enumerate(glider.ribs):
        ribs_sheet[rib_no+1, 0].set_value(rib.name)
        ribs_sheet[rib_no+1, 1].set_value(rib.material_code)

    # panels
    all_panels = sum([cell.panels for cell in glider.cells], [])
    panel_sheet = ezodf.Table(name="material_panels", size=(len(all_panels)+1, 2))

    panel_sheet[0, 0].set_value("Panel")
    panel_sheet[0, 1].set_value("Material")
    for panel_no, panel in enumerate(all_panels):
        panel_sheet[panel_no+1, 0].set_value(panel.name)
        panel_sheet[panel_no+1, 1].set_value(panel.material_code)

    # dribs
    all_dribs = sum([cell.diagonals for cell in glider.cells], [])
    dribs_sheet = ezodf.Table(name="material_dribs", size=(len(all_dribs)+1, 2))

    dribs_sheet[0, 0].set_value("Diagonal")
    dribs_sheet[0, 1].set_value("Material")
    for drib_no, drib in enumerate(all_dribs):
        dribs_sheet[drib_no+1, 0].set_value(drib.name)
        dribs_sheet[drib_no+1, 1].set_value(drib.material_code)

    return ribs_sheet, panel_sheet, dribs_sheet
