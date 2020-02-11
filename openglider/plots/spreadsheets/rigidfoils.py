import ezodf

def get_length_table(glider):

    table = ezodf.Table(name="rigidfoils", size=(500, 500))
    num = 0

    for rib_no, rib in enumerate(glider.ribs):
        num = max(num, len(rib.rigidfoils))
        table[rib_no+1, 0].set_value("Rib_{}".format(rib_no))
        for rigid_no, rigidfoil in enumerate(rib.rigidfoils):
            table[rib_no+1, 2*rigid_no+1].set_value(f"{rigidfoil.start}/{rigidfoil.end}")
            table[rib_no+1, 2*rigid_no+2].set_value(round(1000*rigidfoil.get_length(rib), 1))

    for i in range(num):
        table[0, 2*i+1].set_value("start/stop")
        table[0, 2*i+2].set_value("length")

    return table