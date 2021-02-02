import re
import json
import io
import logging

logger = logging.getLogger(__name__)

def migrate(jsondata, version):
    for migration in migrations:
        if version < migration:
            jsondata = migrations[migration](jsondata)
    
    return jsondata


def migrate_00(jsondata):
    """
    Alter data and return
    :param jsondata:
    :return:
    """
    for node in find_nodes(jsondata, name=r"DrawingArea"):
        node["__class__"] = "Layout"

    return jsondata

def migrate_07(jsondata):
    logger.info("migrating to 0.0.7")
    for curvetype in ("Bezier", "SymmetricBezier", "BSpline", "SymmetricBSpline"):
        for node in find_nodes(jsondata, name="^"+curvetype+"$"):
            node["data"].pop("basefactory")
            node["_type"] = f"{curvetype}Curve"
            node["_module"] = "openglider_cpp.euklid"
    
    return jsondata


def find_nodes(jsondata, name=r".*", module=r".*"):
    """
    Find nodes recursive
    :param name: *to find any
    :param module: *to search all
    :param jsondata:
    :return: list of nodes
    """
    rex_name = re.compile(name)
    rex_module = re.compile(module)
    nodes = []
    if isinstance(jsondata, dict):
        if "_type" in jsondata:
            # node
            if rex_name.match(jsondata["_type"]) and rex_module.match(jsondata["_module"]):
                nodes.append(jsondata)
            else:
                for key, value in jsondata["data"].items():
                    nodes += find_nodes(value, name, module)

        elif isinstance(jsondata, dict):
            for el in jsondata.values():
                nodes += find_nodes(el, name, module)
        elif isinstance(jsondata, str):
            pass
        else:
            try:
                for el in jsondata:
                    nodes += find_nodes(el, name, module)
            except TypeError:
                pass

    return nodes



migrations = {
    "0.0.3": migrate_00,
    "0.0.7": migrate_07
}