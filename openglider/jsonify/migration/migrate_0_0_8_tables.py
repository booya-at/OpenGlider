import logging
import json

from openglider.jsonify.encoder import Encoder
from openglider.jsonify.migration.migration import Migration
from openglider.glider.parametric.table.holes import HolesTable
from openglider.glider.parametric.table.diagonals import DiagonalTable, StrapTable
from openglider.utils.table import Table

logger = logging.getLogger(__name__)

@Migration.add("0.0.8")
def migrate_diagonals(cls, jsondata):
    nodes = cls.find_nodes(jsondata, name=r"ParametricGlider")
    if not nodes:
        return jsondata

    for node in nodes:
        elements = node["data"]["elements"]
        
        holes = elements.get("holes", [])
        table = get_hole_table(holes)
        elements["holes"] = table
        
        diagonals = elements.get("diagonals", [])
        table_diagonals = get_diagonals_table(diagonals)
        elements["diagonals"] = table_diagonals
        
        straps = elements.get("straps", [])
        table_straps = get_straps_table(straps)
        elements["straps"] = table_straps

        materials = elements.pop("materials")
        if materials:
            elements["material_cells"] = materials

        node["data"]["elements"] = json.loads(json.dumps(elements, cls=Encoder))
    
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


    return HolesTable(table)



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

    return DiagonalTable(table)

def get_straps_table(straps):
    table = Table()
    cell_num = max([max(strap["cells"]) for strap in straps])
    straps_per_cell = []

    for _i in range(cell_num+1):
        straps_per_cell.append([])
    
    for strap in straps:
        for cell_no in strap["cells"]:            
            straps_per_cell[cell_no].append((strap["left"], strap["right"], strap["width"]))

    for cell_straps in straps_per_cell:
        cell_straps.sort(key=lambda x: sum(x[:2]))
        
    def find_next_strap(strap, cell_no):
        straps_this = straps_per_cell[cell_no]
        for new_strap in straps_this:
            if strap[1] == new_strap[0]:
                straps_this.remove(new_strap)
                return new_strap

    def add_column(cell_no):
        straps_this = straps_per_cell[cell_no]

        #print("jo", cell_no, straps_this)
        if not straps_this:
            return False

        strap = straps_this.pop(0)

        column = Table()
        column[0, 0] = "STRAP"

        column.insert_row(strap, cell_no+1)


        for cell_no_temp in range(cell_no+1, cell_num):
            strap_next = find_next_strap(strap, cell_no_temp)
            if not strap_next:
                continue
            column.insert_row(strap_next, cell_no_temp+1)
            strap = strap_next

        table.append_right(column)

        return column

    for cell_no in range(cell_num):
        while add_column(cell_no):
            pass
    
    return StrapTable(table)