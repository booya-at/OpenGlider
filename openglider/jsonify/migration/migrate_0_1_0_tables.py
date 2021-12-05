import logging
import json
import copy
from typing import TYPE_CHECKING

from openglider.jsonify.encoder import Encoder
from openglider.jsonify.migration.migration import Migration

if TYPE_CHECKING:
    from openglider.jsonify.migration.migration import Migration

logger = logging.getLogger(__name__)

@Migration.add("0.1.0")
def migrate_attachment_points(cls: "Migration", jsondata):
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
def migrate_tables(cls: "Migration", jsondata):
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


