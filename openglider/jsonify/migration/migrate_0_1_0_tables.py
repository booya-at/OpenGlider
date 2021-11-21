import logging
import json
import copy

from openglider.jsonify.encoder import Encoder
from openglider.jsonify.migration.migration import Migration

logger = logging.getLogger(__name__)

@Migration.add("0.1.")
def migrate_attachment_points(cls, jsondata):
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
def migrate_tables(cls, jsondata):
    nodes = cls.find_nodes(jsondata, name=r"ParametricGlider")
    
    if not nodes:
        return jsondata

    for node in nodes:
        elements = node["data"].pop("elements")

        node["data"]["tables"] = {
            "_type": "GliderTables",
            "_module": "openglider.glider.parametric.table",
            "data": elements
        }

    return jsondata


