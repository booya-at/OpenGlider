import ezodf
import openglider.glider


def export_ods(glider, filename):
    doc = ezodf.newdoc(doctype="ods", filename=filename)
    assert isinstance(glider, openglider.glider.Glider2D)
    cell_no = glider.cell_num // 2 + glider.has_center_cell

    geom_page = ezodf.Sheet(name="geometry", size=(cell_no + 2, 10))

    for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
                     "Y-Rotation-Offset", "merge", "balooning")):
        geom_page.get_cell((0, i)).value = value

    for i in range(1, cell_no+2):
        geom_page.get_cell(i, 0).value = i

    ribs = glider.ribs()
    x = [rib[0][0] for rib in ribs]
    y = [rib[0][1] for rib in ribs]
    chord = [rib[0][1] - rib[1][1] for rib in ribs]
