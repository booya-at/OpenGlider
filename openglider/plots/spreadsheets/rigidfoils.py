from openglider.glider import Glider
from openglider.glider.cell.elements import PanelRigidFoil
from openglider.utils.table import Table


def get_length_table(glider: Glider) -> Table:
    rib_table = get_rib_length_table(glider)
    rib_table.append_right(get_cell_length_table(glider), space=1)

    return rib_table

def get_rib_length_table(glider: Glider) -> Table:
    table = Table()
    num = 0

    for rib_no, rib in enumerate(glider.ribs):
        num = max(num, len(rib.get_rigidfoils()))
        table[rib_no+1, 0] = f"Rib_{rib_no}"
        for rigid_no, rigidfoil in enumerate(rib.get_rigidfoils()):
            table[rib_no+1, 2*rigid_no+1] = f"{rigidfoil.start}/{rigidfoil.end}"
            table[rib_no+1, 2*rigid_no+2] = round(1000*rigidfoil.get_length(rib), 1)

    for i in range(num):
        table[0, 2*i+1] = "start/stop"
        table[0, 2*i+2] = "length"

    return table

def get_cell_length_table(glider: Glider) -> Table:
    table = Table()
    num = 0

    for cell_no, cell in enumerate(glider.cells):
        num = max(num, len(cell.rigidfoils))
        table[cell_no+1, 0] = f"Cell_{cell_no}"
        for rigid_no, rigidfoil in enumerate(cell.rigidfoils):
            table[cell_no+1, 2*rigid_no+1] = f"{rigidfoil.x_start}/{rigidfoil.x_end} ({rigidfoil.y})"
            table[cell_no+1, 2*rigid_no+2] = round(1000*rigidfoil.get_length(cell), 1)

    for i in range(num):
        table[0, 2*i+1] = "start/stop"
        table[0, 2*i+2] = "length"

    return table