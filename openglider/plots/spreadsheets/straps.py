from openglider.glider.cell.elements import TensionStrap
from openglider.utils.table import Table

def get_length_table(glider) -> Table:
    table = Table(name="straps")
    num = 0

    for cell_no, cell in enumerate(glider.cells):
        num = max(num, len(cell.straps))
        table[cell_no+1, 0] = "cell_{}".format(cell_no)
        for strap_no, strap in enumerate(cell.straps):
            strap: TensionStrap
            table[cell_no+1, 2*strap_no+1] = "{}/{}".format(strap.left.center, strap.right.center)
            table[cell_no+1, 2*strap_no+2] = round(1000*strap.get_center_length(cell), 1)

    for i in range(num):
        table[0, 2*i+1] = "pos"
        table[0, 2*i+2] = "length"

    return table