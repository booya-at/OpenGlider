import logging
from typing import TYPE_CHECKING, Any, Literal
from openglider.glider.parametric.table.curve import CurveTable
from openglider.glider.parametric.table.rigidfoil import CellRigidTable, RibRigidTable
from openglider.glider.parametric.table.material import CellClothTable, RibClothTable
from openglider.glider.parametric.table.cell.miniribs import MiniRibTable

from openglider.jsonify.migration.migration import Migration
from openglider.glider.parametric.table.cell.cuts import CutTable
from openglider.utils.table import Table

if TYPE_CHECKING:
    from openglider.jsonify.migration.migration import Migration

logger = logging.getLogger(__name__)

@Migration.add("0.0.9")
def migrate_diagonals(cls: type[Migration], jsondata: Any) -> Any:
    nodes = cls.find_nodes(jsondata, name=r"ParametricGlider")
    if not nodes:
        return jsondata

    for node in nodes:
        logger.info(f"start migration")
        elements = node["data"]["elements"]

        cuts = elements.get("cuts", [])
        cuts_table = get_cuts_table(cuts)
        elements["cuts"] = cuts_table

        material_cells = elements.get("material_cells", [])
        material_table = cls.to_dict(get_materials_table(material_cells, CellClothTable))
        elements["material_cells"] = material_table

        material_ribs = elements.get("material_ribs", [])
        elements["material_ribs"] = cls.to_dict(get_materials_table(material_ribs, RibClothTable))

        logger.info(f"start migration2")
        cell_rigids = elements.get("cell_rigidfoils", [])
        elements["cell_rigidfoils"] = cls.to_dict(get_cell_rigidfoil_table(cell_rigids))

        rib_rigids = elements.get("rigidfoils", [])
        elements["rigidfoils"] = cls.to_dict(get_rib_rigidfoil_table(rib_rigids))

        elements["miniribs"] = cls.to_dict(MiniRibTable(Table()))

        if "curves" not in node["data"]:
            node["data"]["curves"] = cls.to_dict(CurveTable(Table()))

        logger.info(f"done migration")
    
    logger.info(f"start pop")

    for node_type in (r"LowerNode2D", r"UpperNode2D", r"BatchNode2D"):
        for node in cls.find_nodes(jsondata, name=node_type):
            logger.info("jo")
            node["data"].pop("layer")

    logger.info(f"start rename")

    to_rename = [
        ("ballooning", "cell.ballooning"),
        ("holes", "rib.holes"),
        ("diagonals", "cell.diagonals"),
        ("ribs_singleskin", "rib.singleskin")
    ]

    for name, target in to_rename:
        module_name_old = rf"openglider.glider.parametric.table.{name}"
        module_name_new = f"openglider.glider.parametric.table.{target}"
        for node in cls.find_nodes(jsondata, module=module_name_old):
            #print("noooode", node)
            node["_module"] = module_name_new
        
    return jsondata

def get_cell_rigidfoil_table(rigidfoils: list[dict[str, Any]]) -> CellRigidTable:
    table = Table()
    rigidfoils.sort(key=lambda r: r["x_start"])
    for rigidfoil in rigidfoils:
        rigidfoil_table = Table()
        rigidfoil_table[0, 0] = "RIGIDFOIL"

        for cell_no in rigidfoil["cells"]:
            rigidfoil_table[cell_no+1, 0] = rigidfoil["x_start"]
            rigidfoil_table[cell_no+1, 1] = rigidfoil["x_end"]
            rigidfoil_table[cell_no+1, 2] = rigidfoil["y"]
        
        table.append_right(rigidfoil_table)

    return CellRigidTable(table)


def get_rib_rigidfoil_table(rigidfoils: list[dict[str, Any]]) -> RibRigidTable:
    table = Table()

    rigidfoils.sort(key=lambda r: r["start"])
    for rigidfoil in rigidfoils:
        rigidfoil_table = Table()
        rigidfoil_table[0, 0] = "RIGIDFOIL"

        for rib_no in rigidfoil["ribs"]:
            rigidfoil_table[rib_no+1, 0] = rigidfoil["start"]
            rigidfoil_table[rib_no+1, 1] = rigidfoil["end"]
            rigidfoil_table[rib_no+1, 2] = rigidfoil["distance"]
        
        table.append_right(rigidfoil_table)
    
    return RibRigidTable(table)


def get_materials_table(materials: list[list[dict[str, Any]]], _cls: Any) -> Any:
    # Material
    material_table = Table()
    for cell_no, cell in enumerate(materials):
        for part_no, part in enumerate(cell):
            material_name = part
            if isinstance(part, dict):
                material_name = part["data"]["name"]

            material_table[cell_no+1, part_no] = material_name

    for part_no in range(material_table.num_columns):
        material_table[0, part_no] = "MATERIAL"
    
    return _cls(material_table)

def get_cuts_table(cuts: list[dict[str, Any]]) -> CutTable:
    cuts_table = Table()
    cuts_per_cell: list[list[tuple[float, float, str]]] = []

    cell_num = 0
    for cut in cuts:
        cell_num = max(max(cut["cells"])+1, cell_num)


    for cell_no in range(cell_num):
        cuts_this: list[tuple[float, float, str]] = []
        for cut in cuts:
            if cell_no in cut["cells"]:
                cuts_this.append((cut["left"], cut["right"], cut["type"]))

        cuts_this.sort(key=lambda x: sum(x[:2]))
        cuts_per_cell.append(cuts_this)

    def find_next(cut: tuple[float, float, str], cell_no: int) -> tuple[float, float, str] | None:
        cuts_this = cuts_per_cell[cell_no]
        for new_cut in cuts_this:
            if cut[1] == new_cut[0] and new_cut[2] == cut[2]:
                cuts_this.remove(new_cut)
                return new_cut
        
        return None

    def add_column(cell_no: int) -> Table | Literal[False]:
        cuts_this = cuts_per_cell[cell_no]
        if not cuts_this:
            return False

        cut = cuts_this[0]
        column = Table()
        column[0, 0] = cut[2]
        column.insert_row(list(cut[:2]), cell_no+1)
        cuts_this.remove(cut)


        for cell_no_temp in range(cell_no+1, cell_num):
            cut_next = find_next(cut, cell_no_temp)
            if not cut_next:
                continue
            column.insert_row(list(cut_next[:2]), cell_no_temp+1)
            cut = cut_next

        cuts_table.append_right(column)

        return column

    for cell_no in range(cell_num):
        while add_column(cell_no):
            pass

    return CutTable(cuts_table)
