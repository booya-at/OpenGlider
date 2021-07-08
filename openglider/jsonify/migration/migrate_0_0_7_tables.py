from openglider.jsonify.migration.migration import Migration
from openglider.utils.table import Table

@Migration.add("0.0.7")
def migrate_diagonals(cls, jsondata):
    for node in cls.find_nodes(jsondata, name=r"ParametricGlider"):
        elements = node["data"]["elements"]
        holes = elements.get("holes", [])

        table = get_hole_table(holes)

        elements["holes"] = table.__json__()
    
    return jsondata




def get_hole_table(holes):
    table = Table()

    for hole in holes:
        hole_table = Table()

        hole_table[0, 0] = "HOLE"

        for rib_no in hole["ribs"]:
            hole_table[rib_no+1, 0] = hole["pos"]
            hole_table[rib_no+1, 1] = hole["size"]
        
        table.append_right(hole_table)


    return table



def get_diagonals_table(diagonals):
    from openglider.glider.cell.elements import DiagonalRib


    table = Table()
    while diagonals:
        diagonals_this = [diagonals.pop(0)]
        cells = set(diagonals_this[0]["cells"])

        to_remove = []
        for d in diagonals:
            if len(cells.intersection(d["cells"])) == 0:
                diagonals_this.append(d)
                to_remove.append(d)
                cells = cells.union(d["cells"])
        
        for d in to_remove:
            diagonals.remove(d)

        diagonal_table = Table()

        for diagonal in diagonals_this:
            diagonal = copy.copy(diagonal)
            diagonal_table[0, 0] = "QR"
            cells = diagonal.pop("cells")
            _diagonal = DiagonalRib(**diagonal)

            for cell_no in cells:
                # center_left, center_right, width_left, width_right, height_left, height_right

                diagonal_table[cell_no+1, 0] = _diagonal.center_left
                diagonal_table[cell_no+1, 1] = _diagonal.center_right
                diagonal_table[cell_no+1, 2] = _diagonal.width_left
                diagonal_table[cell_no+1, 3] = _diagonal.width_right
                diagonal_table[cell_no+1, 4] = _diagonal.left_front[1]
                diagonal_table[cell_no+1, 5] = _diagonal.right_front[1]

        table.append_right(diagonal_table)

    return table