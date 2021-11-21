import logging
import json
import copy

from openglider.jsonify.encoder import Encoder
from openglider.jsonify.migration.migration import Migration

logger = logging.getLogger(__name__)

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


