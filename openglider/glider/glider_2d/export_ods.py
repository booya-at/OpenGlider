import ezodf
import openglider.glider


def export_ods_2d(glider, filename):
    doc = ezodf.newdoc(doctype="ods", filename=filename)
    assert isinstance(glider, openglider.glider.Glider2D)
    cell_no = glider.cell_num // 2 + glider.has_center_cell

    geom_page = ezodf.Sheet(name="geometry", size=(cell_no + 2, 10))

    # rib_nos
    geom_page[0, 0].set_value("Ribs")
    for i in range(1, cell_no+2):
        geom_page[i, 0].set_value(i)

    shape = glider.half_shape()

    geom_page[0, 1].set_value("Chord")
    for i, chord in enumerate(shape.chords):
        geom_page[i+1, 1].set_value(chord)

    geom_page[0, 2].set_value("Le x (m)")
    geom_page[0, 3].set_value("Le y (m)")
    for i, p in enumerate(shape.front):
        geom_page[i+1, 2].set_value(p[0])
        geom_page[i+1, 3].set_value(p[1])

    doc.sheets.append(geom_page)
    doc.saveas(filename)




# for i, value in enumerate(("Ribs", "Chord", "x: (m)", "y LE (m)", "kruemmung", "aoa", "Z-rotation",
#                      "Y-Rotation-Offset", "merge", "balooning")):
#         geom_page.get_cell((0, i)).value = value
#
#     ribs = glider.ribs()
#     x = [rib[0][0] for rib in ribs]
#     y = [rib[0][1] for rib in ribs]
#     chord = [rib[0][1] - rib[1][1] for rib in ribs]
