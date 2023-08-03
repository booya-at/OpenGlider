from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Any

from openglider.jsonify.encoder import Encoder
from openglider.jsonify.migration.migration import Migration

if TYPE_CHECKING:
    from openglider.jsonify.migration.migration import Migration

logger = logging.getLogger(__name__)

@Migration.add("0.1.0")
def migrate_attachment_points(cls: Migration, jsondata: dict[str, Any]) -> dict[str, Any]:
    nodes = cls.find_nodes(jsondata, name=r"ParametricGlider")
    
    if not nodes:
        return jsondata

    for node in nodes:
        cell_count = node["data"]["shape"]["data"]["cell_num"]

        has_center_cell = bool(cell_count % 2)
        if has_center_cell:
            upper_nodes = cls.find_nodes(node, name=r"UpperNode2D")
            for upper_node in upper_nodes:
                upper_node["data"]["cell_no"] += 1

    return jsondata


@Migration.add("0.1.1")
def migrate_tables(cls: Migration, jsondata: dict[str, Any]) -> dict[str, Any]:
    nodes = cls.find_nodes(jsondata, name=r"ParametricGlider")
    
    if not nodes:
        return jsondata

    for node in nodes:
        elements = node["data"].pop("elements")

        if "singleskin_ribs" in elements:
            table = elements.pop("singleskin_ribs")
            table["_module"] = "openglider.glider.parametric.table.rib.rib"

            elements["rib_modifiers"] = table
        
        if "rigidfoils" in elements:
            elements["rigidfoils_rib"] = elements.pop("rigidfoils")

        if "cell_rigidfoils" in elements:
            elements["rigidfoils_cell"] = elements.pop("cell_rigidfoils")
        
        elements["material_cells"]["_type"] = "CellClothTable"
        elements["material_ribs"]["_type"] = "RibClothTable"

        node["data"]["tables"] = {
            "_type": "GliderTables",
            "_module": "openglider.glider.parametric.table",
            "data": elements
        }


    return jsondata

@Migration.add("0.1.2")
def migrate_table_names(cls: Migration, jsondata: dict[str, Any]) -> dict[str, Any]:
    tables = cls.find_nodes(jsondata, "GliderTables")

    for table in tables:
        table["data"]["material_cells"]["_type"] = "CellClothTable"
        table["data"]["material_ribs"]["_type"] = "RibClothTable"
    
    jsondata = cls.refactor(
        jsondata,
        "openglider.glider.cell.diagonals",
        "DiagonalRib|TensionStrap"
        )
    
    jsondata = cls.refactor(
        jsondata,
        "openglider.glider.cell.rigidfoil",
        "^PanelRigidFoil$"
    )

    jsondata = cls.refactor(
        jsondata,
        "openglider.glider.rib.rigidfoils",
        "^RigidFoil$"
    )

    jsondata = cls.refactor(
        jsondata,
        "openglider.glider.rib.crossports",
        "^RibHole$"
    )

    jsondata = cls.refactor(
        jsondata,
        "openglider.lines.line",
        "^Line$"
    )
    jsondata = cls.refactor(
        jsondata,
        "openglider.lines.node",
        "^Node$"
    )

    
    diagonals = cls.find_nodes(jsondata, name="DiagonalRib")
    for diagonal in diagonals:
        diagonal_data = diagonal["data"]

        for side in ("left", "right"):
            side_front = diagonal_data.pop(f"{side}_front")
            side_back = diagonal_data.pop(f"{side}_back")

            diagonal_data[side] = {
                "_type": "DiagonalSide",
                "_module": "openglider.glider.cell.diagonals",
                "data": {
                    "start_x": side_front[0],
                    "end_x": side_back[0],
                    "start_height": side_front[1],
                    "end_height": side_back[1]
                }
            }
    
    gliders = cls.find_nodes(jsondata, "^Glider$")

    for glider in gliders:
        glider["data"]["cells"] = [
            c["data"] for c in glider["data"]["cells"]
        ]

    projects = cls.find_nodes(jsondata, "^GliderProject$")

    for glider in projects:
        glider["data"].pop("modified", None)

    return jsondata
