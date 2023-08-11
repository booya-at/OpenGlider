from openglider.glider.glider import Glider
from openglider.utils.table import Table

def get_length_table(glider: Glider) -> Table:
    table = Table(name="straps")
    row = 0
    
    table[0, 1] = "name"
    table[0, 2] = "position inner"
    table[0, 3] = "position outer"
    table[0, 4] = "side"
    table[0, 5] = "length"

    for cell in glider.cells:
        table[row, 0] = f"cell_{cell.name}"
        for strap in sorted(cell.straps, key=lambda strap: abs(strap.get_average_x())):
            table[row, 1] = strap.name
            table[row, 2] = f"{abs(strap.left.center.si*100):.0f}%"
            table[row, 3] = f"{abs(strap.right.center.si*100):.0f}%"
            table[row, 4] = "upper" if strap.get_average_x() < 0 else "lower"
            table[row, 5] = f"{strap.get_center_length(cell)*1000:.0f}mm"
            
            row += 1


    return table