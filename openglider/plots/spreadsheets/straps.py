import ezodf

def get_length_table(glider):

    table = ezodf.Table(name="straps", size=(500, 500))
    num = 0

    for cell_no, cell in enumerate(glider.cells):
        num = max(num, len(cell.straps))
        table[cell_no+1, 0].set_value("cell_{}".format(cell_no))
        for strap_no, strap in enumerate(cell.straps):
            table[cell_no+1, 2*strap_no+1].set_value("{}/{}".format(strap.center_left, strap.center_right))
            table[cell_no+1, 2*strap_no+2].set_value(round(1000*strap.get_center_length(cell), 1))

    for i in range(num):
        table[0, 2*i+1].set_value("pos")
        table[0, 2*i+2].set_value("length")

    return table